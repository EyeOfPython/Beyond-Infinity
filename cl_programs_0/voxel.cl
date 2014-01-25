
struct __attribute__((packed)) voxel_t 
{
	char flags;
	float color[3];

	char _pad[3];
};

struct __attribute__((packed)) chunk_t
{
	int level;
	uint voxel_offset;
};

struct __attribute__((packed)) chunk_layer_t
{
	int2 x_bounds;
	int2 y_bounds;
	uint chunk_offset;
};

struct __attribute__((packed)) chunk_array_t
{
	int2 x_bounds;
	int2 y_bounds;
	int2 z_bounds;
	__global struct chunk_layer_t* chunk_layers;
	__global struct chunk_t*       chunks;
	__global struct voxel_t*	   voxel_levels[6];
};

__kernel void init_chunk_array(__global struct chunk_array_t* chunk_array, __global struct chunk_layer_t* chunk_layers, 
							   __global struct chunk_t* chunks, __global struct voxel_t* voxel_level0, __global struct voxel_t* voxel_level1, 
							   __global struct voxel_t* voxel_level2, __global struct voxel_t* voxel_level3, __global struct voxel_t* voxel_level4,
							   __global struct voxel_t* voxel_level5)  
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

__global struct chunk_t* get_chunk(struct chunk_array_t chunk_array, int3 chunk_coords)
{
	if(chunk_coords.z < chunk_array.z_bounds[0] || chunk_coords.z >= chunk_array.z_bounds[1])
		return 0; // z out of z bounds, return NULL

	int offset = chunk_coords.z - chunk_array.z_bounds[0];
	struct chunk_layer_t chunk_layer = chunk_array.chunk_layers[offset];

	if(chunk_coords.x < chunk_layer.x_bounds[0] || chunk_coords.x >= chunk_layer.x_bounds[1] || 
	   chunk_coords.y < chunk_layer.y_bounds[0] || chunk_coords.y >= chunk_layer.y_bounds[1])
		return 0; // x or y out of x or y bounds, return NULL

	int width = chunk_layer.y_bounds[1] - chunk_layer.y_bounds[0];
	offset = (chunk_coords.x - chunk_layer.x_bounds[0]) + width * (chunk_coords.y - chunk_layer.y_bounds[0]);

	return chunk_array.chunks + chunk_layer.chunk_offset + offset;
}

bool _raytrace_chunk_base(struct ray_t ray, float3 start_point, float3 direction, int3 chunk_origin, int chunk_width_log2, int voxel_width, 
						  __global struct voxel_t* voxels, struct raytrace_result_t* result)
{
	
	int i;
	int3 loc = convert_int3( (start_point - convert_float3(chunk_origin))) / voxel_width;

	int chunk_width_voxels = 1 << chunk_width_log2;
	int chunk_width_log2_2 = chunk_width_log2*2;
	int3 step_size = convert_int3(sign(direction));
	int3 end;
	float3 t_max, delta_t;

	for(i = 0; i < 3; ++i)
	{
		if(direction[i] < -epsilon || direction[i] > epsilon)
		{
			if(direction[i] > 0)
			{
				end[i] = chunk_width_voxels;
				t_max[i] = ( floor((start_point[i] + step_size[i] * voxel_width) / voxel_width) * voxel_width - start_point[i] ) / direction[i];
			}
			else
			{
				end[i] = -1;
				t_max[i] = ( ceil((start_point[i] + step_size[i] * voxel_width) / voxel_width) * voxel_width - start_point[i] ) / direction[i];
			}
			delta_t[i] = fabs(voxel_width / direction[i]);
		}
		else
		{
			end[i] = chunk_width_voxels;
			t_max[i] = 1e30f;
			delta_t[i] = 1e30f;
		}
	}

	int w = chunk_width_voxels;
	int w3 = chunk_width_voxels*chunk_width_voxels*chunk_width_voxels;
	while(loc.x != end.x && loc.y != end.y && loc.z != end.z)
	{
		int offset = (loc.z<<chunk_width_log2_2) + (loc.y<<chunk_width_log2) + loc.x;
		//int offset = (loc.z*chunk_width_voxels) * chunk_width_voxels + loc.y*chunk_width_voxels + loc.x;
		if(offset < w3)
		{
			__global struct voxel_t* voxel = voxels + offset;
			if(voxel->flags & 0x1) // non empty block found
			{
				struct aacube_t voxel_cube = { convert_float3(loc * voxel_width + chunk_origin), voxel_width };
				bool b = raytrace_aacube(ray, voxel_cube, result);
				result->loc = loc;
				return true;
			}
		}

		if(t_max.x < t_max.y)
		{
			if(t_max.x < t_max.z)
			{
				loc.x   += step_size.x;
				t_max.x += delta_t.x;
			}
			else
			{
				loc.z   += step_size.z;
				t_max.z += delta_t.z;
			}
		}
		else
		{
			if(t_max.y < t_max.z)
			{
				loc.y   += step_size.y;
				t_max.y += delta_t.y;
			}
			else
			{
				loc.z   += step_size.z;
				t_max.z += delta_t.z;
			}
		}
	}
	return false;
}

__constant int chunk_width = 32;

bool raytrace_chunk(struct ray_t ray, int3 chunk_origin, struct chunk_array_t chunk_array, __global struct chunk_t* chunk, struct raytrace_result_t* result)
{
	struct aacube_t chunk_cube = { convert_float3(chunk_origin), chunk_width - epsilon };
	struct raytrace_result_t chunk_result;

	bool intersection = raytrace_aacube(ray, chunk_cube, &chunk_result);

	if(!intersection)
		return false;
	intersection = _raytrace_chunk_base(ray, chunk_result.point, ray.direction, chunk_origin, 5 - chunk->level, 1 << chunk->level, chunk_array.voxel_levels[chunk->level] + chunk->voxel_offset, result);
	return intersection;
}

bool raytrace_chunk_array(struct ray_t ray, struct chunk_array_t chunk_array, struct raytrace_result_t* result)
{
	int i;
	int3 loc = convert_int3_rtn( ray.origin / chunk_width );

	int3 step_size = convert_int3(sign(ray.direction));
	int3 end;
	float3 t_max, delta_t;

	for(i = 0; i < 3; ++i)
	{
		int2 bounds = *((int2*)&chunk_array+i);
		if(ray.direction[i] < -epsilon || ray.direction[i] > epsilon)
		{
			if(ray.direction[i] > 0)
			{
				end[i] = bounds[1];
				t_max[i] = ( floor((ray.origin[i] + step_size[i] * chunk_width) / chunk_width) * chunk_width - ray.origin[i] ) / ray.direction[i];
			}
			else
			{
				end[i] = bounds[0] - 1;
				t_max[i] = ( ceil((ray.origin[i] + step_size[i] * chunk_width) / chunk_width) * chunk_width - ray.origin[i] ) / ray.direction[i];
			}
			delta_t[i] = fabs(chunk_width / ray.direction[i]);
		}
		else
		{
			end[i] = bounds[1];
			t_max[i] = 1e30f;
			delta_t[i] = 1e30f;
		}
	}

	while(loc.x != end.x && loc.y != end.y && loc.z != end.z)
	{
		// check chunk
		__global struct chunk_t* chunk = get_chunk(chunk_array, loc);
		if(chunk != 0)
		{
			float3 t0;
			float t;
			for(i = 0; i < 3; ++i)
				t0[i] = t0[i] >= 1e30f ? -1e30f : t0[i];

			if(t_max.x > t_max.y)
			{
				if(t_max.x > t_max.z)
					t = t_max.x;
				else
					t = t_max.z;
			}
			else
			{
				if(t_max.y > t_max.z)
					t = t_max.y;
				else
					t = t_max.z;
			}

			float3 start_point = ray.origin + ray.direction * t;

			bool intersection = raytrace_chunk(ray, loc * chunk_width, chunk_array, chunk, result);
			if(intersection)
				return true;
		}

		if(t_max.x < t_max.y)
		{
			if(t_max.x < t_max.z)
			{
				loc.x   += step_size.x;
				t_max.x += delta_t.x;
			}
			else
			{
				loc.z   += step_size.z;
				t_max.z += delta_t.z;
			}
		}
		else
		{
			if(t_max.y < t_max.z)
			{
				loc.y   += step_size.y;
				t_max.y += delta_t.y;
			}
			else
			{
				loc.z   += step_size.z;
				t_max.z += delta_t.z;
			}
		}
	}
	return false;
}

__kernel void test_kernel(__global char *test_data)
{
	struct raytrace_result_t result;
	//_raytrace_chunk_base((float3)(0), normalize((float3)(1,1,1.4)), (int3)(0), 10, 1, test_data, 0, &result);
}

void build_chunk_bitmap(__private uchar* bitmap, struct chunk_array_t chunk_array, __global struct chunk_t* chunk)
{
	__global struct voxel_t* voxel = chunk_array.voxel_levels[chunk->level] + chunk->voxel_offset;

	int max_o = 32 >> chunk->level;
	max_o = max_o*max_o*max_o;
	for(int i = 0; i<max_o/8; ++i)
	{
		for(uchar j = 0; j<8; ++j)
		{
			*bitmap |= (uchar)(voxel->flags & 0x1) << j;
			++voxel;
		}
		++bitmap;
	}
	
}

__kernel void calculate_chunk_levels(__global struct chunk_array_t* chunk_array_p)
{
	
}

__kernel void write_height_map(__global struct chunk_array_t* chunk_array_p, __global int* height_map)
{
	int x = get_global_id(0);
	int y = get_global_id(1);
	int z = get_global_id(2);

	struct chunk_array_t chunk_array = *chunk_array_p;
	__global struct chunk_t* chunk = get_chunk(chunk_array, (int3)(x/32, y/32, z/32));
	int offset = (z%32)*32*32 + (y%32)*32 + (x%32);
	__global struct voxel_t* voxel = chunk_array.voxel_levels[chunk->level] + chunk->voxel_offset + offset;
	if(height_map[x + y*256] >= z)
		voxel->flags = 1;
	else
		voxel->flags = 0;
}
