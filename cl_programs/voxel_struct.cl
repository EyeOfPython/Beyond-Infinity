
#define chunk_width 32

struct __attribute__((packed)) _voxel_t 
{
	char flags;
	float color[3];

	char _pad[3];
};

typedef struct _voxel_t voxel_t;

struct __attribute__((packed)) _chunk_t
{
	int level;
	uint voxel_offset;
};

typedef struct _chunk_t chunk_t;

struct __attribute__((packed)) _chunk_layer_t
{
	int2 x_bounds;
	int2 y_bounds;
	uint chunk_offset;
};

typedef struct _chunk_layer_t chunk_layer_t;

struct __attribute__((packed)) _chunk_array_t
{
	int2 x_bounds;
	int2 y_bounds;
	int2 z_bounds;
	__global chunk_layer_t* chunk_layers;
	__global chunk_t*       chunks;
	__global voxel_t*	    voxel_levels[6];
};

typedef struct _chunk_array_t chunk_array_t;