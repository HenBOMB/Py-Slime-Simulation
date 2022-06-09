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


struct Food
{
    int2 pos;
    float radius;
    float weight;
};

Buffer<float> time : register(t2);

Texture2D<float4> trailMapIn : register(t0);
StructuredBuffer<Agent> agentsIn : register(t1);
StructuredBuffer<Species> species : register(t3);
StructuredBuffer<Food> food : register(t4);
Texture2D<float4> agentsTexture : register(t5);

RWTexture2D<float4> trailMapOut : register(u0);
RWStructuredBuffer<Agent> agentsOut : register(u1);
RWTexture2D<float4> agentsTextureOut : register(u2);

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
            sum += trailMapIn[uint2(clamp(sensor.x + x, 0, !WIDTH - 1), clamp(sensor.y + y, 0, !HEIGHT - 1)).xy];
            // float4 res = trailMapIn[uint2(clamp(sensor.x + x, 0, !WIDTH - 1), clamp(sensor.y + y, 0, !HEIGHT - 1)).xy];
            // sum += dot(
            //     res,
            //     weight
            // );
        }
        
    return sum;
}

float distance(int2 from, int2 to)
{
    return sqrt((from.x - to.x) * (from.x - to.x)) + sqrt((from.y - to.y) * (from.y - to.y));
}

float2 clamp_vector(float2 endPoint, float2 midPoint, float maxDistance)
{
    float dist = distance(midPoint, endPoint);
    if (dist > maxDistance)
    {
        float2 dirVector = endPoint - midPoint;
        dirVector = normalize(dirVector);
        return (dirVector * maxDistance) + midPoint;   
    }

    return endPoint;
}

[numthreads(!AGENT_THREADS,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    if (tid.x >= !NUM_AGENTS) return;

    if(!agentsIn[tid.x].alive) return;

    Species s = species[agentsIn[tid.x].speciesIndex];
    
    float angle = agentsIn[tid.x].angle;
    float2 pos = agentsIn[tid.x].pos;
    float2 dir = float2(cos(angle), sin(angle)) * s.ss;

    uint h = hash(pos.y * !WIDTH + pos.x + angle + hash(tid.x + time[0] * 100000));

    // SENSOR //
    
	float forward   = sense(agentsIn[tid.x], s,     0);
	float right     = sense(agentsIn[tid.x], s,  s.sa);
	float left      = sense(agentsIn[tid.x], s, -s.sa);
	
    float rng = 1;//rand(h);

    if(forward > right && forward > left)                   angle += 0;
    else if(forward < right && forward < left && rng == 1)  angle += rand(h) > 0.5? s.ra : -s.ra;
    else if(forward < right && forward < left && rng != 1)  angle += (rng - .5) * 2 * s.ra;
    else if(left > right)                                   angle -= s.ra * rng;
    else if(right > left)                                   angle += s.ra * rng;
    
    // MOTOR

    // Attempt to move forward one step in the current direction
    pos += dir;
    int2 coord = int2(pos);

    // If next site is occupied
    // Remain in it's current position, no chemoattractant is deposited, and a new orientation is randomly selected
    if(!!AGENT_OVERLAPPING && agentsTexture[coord.xy].r != 0)
    {
        agentsOut[tid.x].pos = agentsIn[tid.x].pos;
        agentsOut[tid.x].angle = rand(hash(h)) * 2 * 3.1415;
        agentsOut[tid.x].speciesIndex = agentsIn[tid.x].speciesIndex;
        agentsOut[tid.x].alive = agentsIn[tid.x].alive;
        agentsTextureOut[int2(agentsIn[tid.x].pos).xy] = 1;
        return;
    }

    agentsTextureOut[int2(agentsIn[tid.x].pos).xy] = 0;
    agentsTextureOut[coord.xy] = 1;

    float2 mid = float2(!WIDTH/2., !HEIGHT/2.);

    if(!RADIAL_BOUNDARY && distance(pos, mid) >= mid.y - !BORDER * 2)
    {
        pos = clamp_vector(pos, mid, mid.y - !BORDER * 2);
        angle = rand(hash(h)) * 2 * 3.1415;
    }
    // Clamp to bounds
    if (!!RADIAL_BOUNDARY && (pos.x < !BORDER || pos.x >= !WIDTH - !BORDER || pos.y < !BORDER || pos.y >= !HEIGHT - !BORDER))
    {
        pos.x = clamp(pos.x, 0, !WIDTH - 1 - !BORDER);
        pos.y = clamp(pos.y, 0, !HEIGHT - 1 - !BORDER);
        angle = rand(hash(h)) * 2 * 3.1415;
    }
    // Deposit a constant chemoattractant value
    else
    {
        float weight = 0.1;

        for(int i=0; i<!NUM_FOOD; i++)
        {
            if(distance(coord, food[i].pos) < food[i].radius)
            {
                weight = food[i].weight;
                break;
            }
        }
		trailMapOut[coord] = clamp(s.mask, 0, 1) * weight * 5;
    }

    // Update the agents

    agentsOut[tid.x].pos = pos;
    agentsOut[tid.x].angle = angle;
    agentsOut[tid.x].speciesIndex = agentsIn[tid.x].speciesIndex;
    agentsOut[tid.x].alive = agentsIn[tid.x].alive;
}