
global chunk_t* get_chunk(chunk_array_t chunk_array, int3 chunk_coords)
{
	if(chunk_coords.z < chunk_array.z_bounds[0] || chunk_coords.z >= chunk_array.z_bounds[1])
		return 0; // z out of z bounds, return NULL

	int offset = chunk_coords.z - chunk_array.z_bounds[0];
	chunk_layer_t chunk_layer = chunk_array.chunk_layers[offset];

	if(chunk_coords.x < chunk_layer.x_bounds[0] || chunk_coords.x >= chunk_layer.x_bounds[1] || 
	   chunk_coords.y < chunk_layer.y_bounds[0] || chunk_coords.y >= chunk_layer.y_bounds[1])
		return 0; // x or y out of x or y bounds, return NULL

	int width = chunk_layer.y_bounds[1] - chunk_layer.y_bounds[0];
	offset = (chunk_coords.x - chunk_layer.x_bounds[0]) + width * (chunk_coords.y - chunk_layer.y_bounds[0]);

	return chunk_array.chunks + chunk_layer.chunk_offset + offset;
}

bool _raytrace_chunk_base(ray_t ray, float3 start_point, float3 direction, int3 chunk_origin, int chunk_width_log2, int voxel_width, 
						  global voxel_t* voxels, raytrace_result_t* result)
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
			global voxel_t* voxel = voxels + offset;
			if(voxel->flags & 0x1) // non empty block found
			{
				aacube_t voxel_cube = { convert_float3(loc * voxel_width + chunk_origin), voxel_width };
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

bool raytrace_chunk(ray_t ray, int3 chunk_origin, chunk_array_t chunk_array, global chunk_t* chunk, raytrace_result_t* result)
{
	aacube_t chunk_cube = { convert_float3(chunk_origin), chunk_width - epsilon };
	raytrace_result_t chunk_result;

	bool intersection = raytrace_aacube(ray, chunk_cube, &chunk_result);

	if(!intersection)
		return false;
	return true;
	//intersection = _raytrace_chunk_base(ray, chunk_result.point, ray.direction, chunk_origin, 5 - chunk->level, 1 << chunk->level, chunk_array.voxel_levels[chunk->level] + chunk->voxel_offset, result);
	//return intersection;
}

bool raytrace_chunk_array(ray_t ray, chunk_array_t chunk_array, raytrace_result_t* result)
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
		global chunk_t* chunk = get_chunk(chunk_array, loc);
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
