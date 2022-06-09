Texture2D<float4> inTexture : register(t0);

RWTexture2D<float4> outTexture : register(u0);

[numthreads(32,32,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
	if (tid.x < 0 || tid.x >= !WIDTH || tid.y < 0 || tid.y >= !HEIGHT) return;

	float4 sum = 0;
    for (int x = -3; x <= 3; x++)
        for (int y = -3; y <= 3; y++)
            sum += inTexture[int2(clamp(tid.x + x, 0, !WIDTH - 1), clamp(tid.y + y, 0, !HEIGHT - 1)).xy];
            
	outTexture[tid.xy] = sum / 49;
}