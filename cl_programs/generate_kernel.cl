
kernel void write_height_map(global chunk_array_t* chunk_array_p, global int* height_map)
{
	int x = get_global_id(0);
	int y = get_global_id(1);
	int z = get_global_id(2);

	chunk_array_t chunk_array = *chunk_array_p;
	global chunk_t* chunk = get_chunk(chunk_array, (int3)(x/32, y/32, z/32));
	int offset = (z%32)*32*32 + (y%32)*32 + (x%32);
	global voxel_t* voxel = chunk_array.voxel_levels[chunk->level] + chunk->voxel_offset + offset;
	
	voxel_t v = chunk_array.voxel_levels[chunk->level][0];
	//chunk_array_p->x_bounds = chunk_array.chunk_layers[0].x_bounds;//chunk->level;//chunk->voxel_offset;
	//chunk_array_p->y_bounds = chunk_array.chunk_layers[0].y_bounds;
	if(height_map[x + y*256] >= z)
		voxel->flags = 1;
	else
		voxel->flags = 0;
}