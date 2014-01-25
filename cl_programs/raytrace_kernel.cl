#include "math.cl"
#include "raytrace_struct.cl"
#include "raytrace.cl"

kernel void init_chunk_array(global chunk_array_t* chunk_array, global chunk_layer_t* chunk_layers, 
							   global chunk_t* chunks, global voxel_t* voxel_level0, global voxel_t* voxel_level1, 
							   global voxel_t* voxel_level2, global voxel_t* voxel_level3, global voxel_t* voxel_level4,
							   global voxel_t* voxel_level5)  
{
	chunk_array->chunk_layers = chunk_layers;
	chunk_array->chunks = chunks;
	chunk_array->voxel_levels[0] = voxel_level0;
	chunk_array->voxel_levels[1] = voxel_level1;
	chunk_array->voxel_levels[2] = voxel_level2;
	chunk_array->voxel_levels[3] = voxel_level3;
	chunk_array->voxel_levels[4] = voxel_level4;
	chunk_array->voxel_levels[5] = voxel_level5;
}

kernel void raytrace( image2d_t write_only canvas, global camera_t* cameras, global chunk_array_t* chunk_array_p )
{
	int x = get_global_id(0);
    int y = get_global_id(1);
    int2 coord = (int2)(x,y);
    int2 framesize = (int2)(get_global_size(0), get_global_size(1));
    
    camera_t camera = cameras[0];
	chunk_array_t chunk_array = chunk_array_p[0];
    
    float2 ratio = convert_float2(coord)/convert_float2(framesize);
    float xpart = camera.bounds.left + ratio.x * (camera.bounds.right  - camera.bounds.left);
    float ypart = camera.bounds.top  + ratio.y * (camera.bounds.bottom - camera.bounds.top);

	ray_t ray;
    ray.origin    = camera.position.xyz;
    ray.direction = rotate_vector(camera.orientation, normalize((float3)(xpart, camera.warp, -ypart)));
    
    float3 color = {0,0,0};
    raytrace_result_t result;
	result.t = 1e20f;

	bool intersection = false;
	//intersection = raytrace_chunk_array(ray, chunk_array, &result);
	intersection = raytrace_chunk(ray, (int3)(1,1,1), chunk_array, chunk_array.chunks, &result);

	if(intersection)
		color = (float3)((result.loc.z + 4) / 32.f);

	write_imagef( canvas, (int2)(x, y), (float4)(color, 1) );
}