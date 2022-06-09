struct Agent
{
    float2 pos;
    float angle;
    uint speciesIndex;
    bool alive;
};

StructuredBuffer<Agent> agents : register(t0);

RWTexture2D<float4> destinationTexture : register(u0);

[numthreads(!AGENT_THREADS,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    if (tid.x < 0 || tid.x >= !WIDTH || tid.y < 0 || tid.y >= !HEIGHT) return;
    if(!agents[tid.x].alive) return;
    destinationTexture[int2(agents[tid.x].pos.x, agents[tid.x].pos.y).xy] = 1;
}