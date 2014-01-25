
struct __attribute__((packed))
_aacube_t 
{
	float3 origin;
	float width; // normals predefined
};

typedef struct _aacube_t aacube_t;


struct __attribute__((packed))
_aabb_t
{
	float3 origin;
	float3 size; // normals predefined 
};

typedef struct _aabb_t aabb_t;

struct __attribute__((packed))
_box_t
{
	float3 center;
	float3 half_size;
	float3 __attribute__((packed)) normals[3]; // and all mirrored normals
};

typedef struct _box_t box_t;


struct __attribute__((packed))
_sphere_t 
{
    float3 center;
    float radius; // normals calculated
};

typedef struct _sphere_t sphere_t;


struct 
_triangle_t
{
	float3 points[3]; // normal calculated
};

typedef struct _triangle_t triangle_t;

struct 
_triangle_strip_t
{
	
};

typedef struct _triangle_strip_t triangle_strip_t;

enum obj_type
{
	OBJ_AACUBE = 1,
	OBJ_AABB,
	OBJ_BOX,
	OBJ_SPHERE
};