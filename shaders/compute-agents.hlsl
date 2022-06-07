struct Agent
{
    float2 pos;
    float angle;
};

Buffer<float> time : register(t2);

Texture2D<float4> trailMapIn : register(t0);
StructuredBuffer<Agent> agentsIn : register(t1);

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

float sense(Agent agent, float sensor_angle_offset)
{
    float sensor_angle = agent.angle + sensor_angle_offset;
    float2 sensor = float2(
        agent.pos.x + cos(sensor_angle) * !SO, 
        agent.pos.y + sin(sensor_angle) * !SO);

    float sum = 0;

	for(int x = -!SW; x <= !SW; x++)
    {
	    for(int y = -!SW; y <= !SW; y++)
        {
            sum += trailMapIn[uint2(
                int(clamp(sensor.x + x, 0, !WIDTH - 1)),
                int(clamp(sensor.y + y, 0, !HEIGHT - 1))).xy];
        }  
    }
        
    return sum;
}

[numthreads(16,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    float angle = agentsIn[tid.x].angle;
    float2 pos = agentsIn[tid.x].pos;

    uint h = hash(pos.y * !WIDTH + pos.y + angle + hash(tid.x + time[0] * 100000));

    // SENSOR
    
	float forward   = sense(agentsIn[tid.x],    0);
	float left      = sense(agentsIn[tid.x],  !SA);
	float right     = sense(agentsIn[tid.x], -!SA);
	
	if(forward > left && forward > right)       angle += 0;
	else if(forward < left && forward < right)  angle += rand(hash(h)) > 0.5? !RA : -!RA;
	else if(right > left)                       angle -= !RA;
	else if(left > right)                       angle += !RA;

    // MOTOR

    pos += float2(cos(angle), sin(angle)) * !SS;
    
    if (pos.x < 0 || pos.x >= !WIDTH || pos.y < 0 || pos.y >= !HEIGHT)
    {
        pos.x = clamp(pos.x, 0, !WIDTH - 1);
        pos.y = clamp(pos.y, 0, !HEIGHT - 1);
        angle = rand(h) * 2 * 3.1415;
    }
    else trailMapOut[int2(pos).xy] = 1;

    agentsOut[tid.x].pos = pos;
    agentsOut[tid.x].angle = angle;
}