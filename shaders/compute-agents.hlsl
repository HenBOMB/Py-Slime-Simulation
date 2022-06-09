struct Agent
{
    float2 pos;
    float angle;
    uint speciesIndex;
    bool alive;
};

struct Species
{
    float sa;
    float ra;
    float so;
    float ss;
    float sw;
    float4 color;
    int4 mask;
};


Buffer<float> time : register(t2);

Texture2D<float4> trailMapIn : register(t0);
StructuredBuffer<Agent> agentsIn : register(t1);
StructuredBuffer<Species> species : register(t3);

RWTexture2D<float4> trailMapOut : register(u0);
RWStructuredBuffer<Agent> agentsOut : register(u1);

// https://gist.github.com/keijiro/24f9d505fac238c9a2982c0d6911d8e3
// https://www.cs.ubc.ca/~rbridson/docs/schechter-sca08-turbulence.pdf
// Hash function from H. Schechter & R. Bridson, goo.gl/RXiKaH
uint hash(uint s)
{
    s ^= 2747636419u;
    s *= 2654435769u;
    s ^= s >> 16;
    s *= 2654435769u;
    s ^= s >> 16;
    s *= 2654435769u;
    return s;
}

float rand(uint seed)
{
    return float(hash(seed)) / 4294967295.0; // 2^32-1
}

float sense(Agent agent, Species s, float sensor_angle_offset)
{
    float sensor_angle = agent.angle + sensor_angle_offset;
    float2 sensor = float2(
        agent.pos.x + cos(sensor_angle) * s.so, 
        agent.pos.y + sin(sensor_angle) * s.so);

    int4 weight = s.mask * 2 - 1;
    float sum = 0;

	for(int x = -s.sw; x <= s.sw; x++)
	    for(int y = -s.sw; y <= s.sw; y++)
        {
            float4 res = trailMapIn[uint2(clamp(sensor.x + x, 0, !WIDTH - 1), clamp(sensor.y + y, 0, !HEIGHT - 1)).xy];
            if(!HARD_AVOIDANCE && ceil(res.r) + ceil(res.g) + ceil(res.b) > 1) return -1;
            sum += dot(
                res,
                weight
            );
        }
        
    return sum;
}

[numthreads(32,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    if (tid.x >= !NUM_AGENTS) return;

    if(!agentsIn[tid.x].alive) return;

    Species s = species[agentsIn[tid.x].speciesIndex];
    
    float angle = agentsIn[tid.x].angle;
    float2 pos = agentsIn[tid.x].pos;

    uint h = hash(pos.y * !WIDTH + pos.x + angle + hash(tid.x + time[0] * 100000));

    // SENSOR
    
	float forward   = sense(agentsIn[tid.x], s,     0);
	float right     = sense(agentsIn[tid.x], s,  s.sa);
	float left      = sense(agentsIn[tid.x], s, -s.sa);
	
    float rng = rand(h);

    if(!HARD_AVOIDANCE)
    {
        float prevAngle = -100;

        if(forward > right && forward > left)
        {
            if(forward < 0) prevAngle = angle;
        }
        else if(forward < right && forward < left)
        {
            if(rng == 1) angle += (rng - .5) * 2 * s.ra;
            else angle += rand(h) > 0.5? s.ra : -s.ra;
            if(right < 0 || left < 0) prevAngle = angle;
        }
        else if(left > right)
        {
            angle -= s.ra * rng;
            if(left < 0) prevAngle = angle;
        }
        else if(right > left)
        {
            angle += s.ra * rng;
            if(right < 0) prevAngle = angle;
        }

        // MOTOR
        if(angle != prevAngle) pos += float2(cos(angle), sin(angle)) * s.ss;
    }
    else
    {
        if(forward > right && forward > left)                   angle += 0;
        else if(forward < right && forward < left && rng == 1)  angle += rand(h) > 0.5? s.ra : -s.ra;
        else if(forward < right && forward < left && rng != 1)  angle += (rng - .5) * 2 * s.ra;
        else if(left > right)                                   angle -= s.ra * rng;
        else if(right > left)                                   angle += s.ra * rng;

        // MOTOR
        pos += float2(cos(angle), sin(angle)) * s.ss;
    }

    // MOTOR
    
    if (pos.x < 0 || pos.x >= !WIDTH || pos.y < 0 || pos.y >= !HEIGHT)
    {
        pos.x = clamp(pos.x, 0, !WIDTH - 1);
        pos.y = clamp(pos.y, 0, !HEIGHT - 1);
        angle = rand(hash(h)) * 2 * 3.1415;
    }
    else
    {
        int2 coord = int2(pos);
        float4 res = min(1, trailMapOut[coord] + s.mask * 0.08);
        
        if(!DIE_ON_TRAPPED) // give the agents some time to spread out
        {
            if(ceil(res.r) + ceil(res.g) + ceil(res.b) > 1 && time[0] > !DEATH_TIME)
            {
                agentsOut[tid.x].alive = false;
                return;
            }
            else
            {
		        trailMapOut[coord] = res;
            }
        }
        else
        {
		    trailMapOut[coord] = res;
        }
    }

    agentsOut[tid.x].pos = pos;
    agentsOut[tid.x].angle = angle;
    agentsOut[tid.x].speciesIndex = agentsIn[tid.x].speciesIndex;
    agentsOut[tid.x].alive = agentsIn[tid.x].alive;
}