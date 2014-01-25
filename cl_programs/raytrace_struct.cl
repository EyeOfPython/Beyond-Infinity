
#define epsilon 0.00001f

struct _ray_t 
{
    float3 origin;
    float3 direction;
};

typedef struct _ray_t ray_t;

struct _raytrace_result_t 
{
	float t;
	float3 point;
	float3 normal;
	__global struct reference_t* object;
	int reason; // test data
	int3 loc;
};

typedef struct _raytrace_result_t raytrace_result_t;

struct __attribute__((packed))
_reference_t
{
	short type;
	uint  offset;
};

typedef struct _reference_t reference_t;

struct 
_camera_t 
{
    float3 position;
    float4 orientation;
    struct {
		float left; float right;
		float bottom; float top;
    } bounds;
	float warp;
};

typedef struct _camera_t camera_t;


struct 
_point_light_t
{
	float4 position;
	float4 color;
};

typedef struct _point_light_t point_light_t;


struct 
_directional_light_t
{
	float4 direction;
	float4 color;
};

typedef struct _directional_light_t directional_light_t;


enum light_type
{
	LIGHT_DIRECTIONAL = 1,
	LIGHT_POINT = 2
};

