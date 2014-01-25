struct ray_t 
{
    float3 origin;
    float3 direction;
};

struct __attribute__((packed))
reference_t
{
	short type;
	uint  offset;
};

struct __attribute__((packed))
aacube_t 
{
	float3 origin;
	float width; // normals predefined
};

struct __attribute__((packed))
aabb_t
{
	float3 origin;
	float3 size; // normals predefined 
};

struct __attribute__((packed))
box_t
{
	float3 center;
	float3 half_size;
	float3 __attribute__((packed)) normals[3]; // and all mirrored normals
};

struct __attribute__((packed))
sphere_t 
{
    float3 center;
    float radius; // normals calculated
};

struct triangle_t
{
	float3 points[3]; // normal calculated
};

struct triangle_strip_t
{
	
};

enum obj_type
{
	OBJ_AACUBE = 1,
	OBJ_AABB,
	OBJ_BOX,
	OBJ_SPHERE
};

struct camera_t 
{
    float3 position;
    float4 orientation;
    struct {
		float left; float right;
		float bottom; float top;
    } bounds;
	float warp;
};

struct point_light_t
{
	float4 position;
	float4 color;
};

struct directional_light_t
{
	float4 direction;
	float4 color;
};

enum light_type
{
	LIGHT_DIRECTIONAL = 1,
	LIGHT_POINT = 2
};

float3 sphere_get_normal_at(struct sphere_t sphere, float3 pos)
{
    return normalize( pos - sphere.center );
}