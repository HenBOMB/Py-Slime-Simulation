struct Agent
{
    float2 pos;
    float angle;
};

StructuredBuffer<Agent> agentsIn : register(t0);

RWTexture2D<float4> trailMapOut : register(u0);

[numthreads(16,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    trailMapOut[int2(agentsIn[tid.x].pos.x, agentsIn[tid.x].pos.y).xy] = 1;
}