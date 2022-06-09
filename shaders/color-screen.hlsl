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

Texture2D<float4> trailMap : register(t0);
Texture2D<float4> agentsTexture : register(t1);
StructuredBuffer<Species> species : register(t2);
Texture2D<float4> blurTexture : register(t3);
StructuredBuffer<Food> foods : register(t4);

RWTexture2D<float4> displayTexture : register(u0);
RWTexture2D<float4> agentsTextureOut : register(u1);

float distance(int2 from, int2 to)
{
    return sqrt((from.x - to.x) * (from.x - to.x)) + sqrt((from.y - to.y) * (from.y - to.y));
}

[numthreads(!TEXTURE_THREADS,!TEXTURE_THREADS,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
	if (tid.x < 0 || tid.x >= !WIDTH || tid.y < 0 || tid.y >= !HEIGHT) return;

	if(!DRAW_AGENTS_ONLY)
	{
		displayTexture[tid.xy] = agentsTexture[tid.xy];
		// agentsTextureOut[tid.xy] = 0;
		return;
	}

	float4 color = 0;

	for(int i=0; i<!NUM_SPECIES; i++)
		color += species[i].color * dot(trailMap[tid.xy], int4(i==0, i==1, i==2, i==3)); 

	if(!DRAW_FOODS)
	{
		for(int i=0; i<!NUM_FOODS; i++)
		{
			if(distance(tid.xy, foods[i].pos) < foods[i].radius)
			{
				color += 0.2;
				break;
			}
		}
	}

	displayTexture[tid.xy] = saturate(color + blurTexture[tid.xy]);
	// agentsTextureOut[tid.xy] = 0;

	// float mask = (trailMap[tid.xy].r + trailMap[tid.xy].g + trailMap[tid.xy].b) / 3;

	// Obsolete ->

	// float sum = 0;

	// for (int x = -5; x <= 5; x++)
	// 	for (int y = -5; y <= 5; y++)
	// 		sum += trailMap[uint2(min(!WIDTH-1, max(0, tid.x + x)), min(!HEIGHT-1, max(0, tid.y + y))).xy];

	// float sub = 100;
	// float mask = max(sum - sub, 0) / (121 - sub);
	// mask = saturate(mask);

	// float4 color = !DRAW_COLOR;
	// float4 color2 = saturate(color - .4);
	// color2.a = 1;

	// displayTexture[tid.xy] = lerp(0, color2, trailMap[tid.xy].r * trailMap[tid.xy].r);
	// // displayTexture[tid.xy] = lerp(color2, color, trailMap[tid.xy].r) * trailMap[tid.xy].r;

	// displayTexture[tid.xy] = lerp(displayTexture[tid.xy], displayTexture[tid.xy] * 2, mask);

	// displayTexture[tid.xy] = saturate(displayTexture[tid.xy] + displayTexture[tid.xy] * agentsTexture[tid.xy]);

	// agentsTexture[tid.xy] = agentsTexture[tid.xy] * (1 - !DECAY_RATE);
}