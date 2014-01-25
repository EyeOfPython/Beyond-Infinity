#include "solver.cl"
#include "objects.cl"

__constant float epsilon = 0.00001f;

struct raytrace_result_t 
{
	float t;
	float3 point;
	float3 normal;
	__global struct reference_t* object;
	int reason; // test data
	int3 loc;
};

bool raytrace_sphere(struct ray_t ray, struct sphere_t sphere, struct raytrace_result_t* result)
{
    float3 rel_pos = ray.origin - sphere.center;
    float sq = sphere.radius*sphere.radius;
    float a,b,c;
    a = dot( ray.direction, ray.direction );
    b = 2 * dot( rel_pos, ray.direction );
    c = dot( rel_pos, rel_pos ) - sq;
          
    float t1, t2;
          
    int roots = quadratic_roots(a, b, c, &t1, &t2);
         
    if(roots > 0 && t1 > 0)
	{
		float t = t1;
		float3 p = ray.origin + ray.direction * t;
		result->t = t;
		result->point = p;
		result->normal = sphere_get_normal_at(sphere, p);
		return true;
    }
    else
		return false;
}

bool raytrace_triangle(struct ray_t ray, struct triangle_t triangle, struct raytrace_result_t* result)
{
	float3 edge1, edge2;
	float3 p, q, r;
	float det, inv_det, u, v, t;

	edge1 = triangle.points[1] - triangle.points[0];
	edge2 = triangle.points[2] - triangle.points[0];

	p = cross(ray.direction, edge2);
	det = dot(edge1, p);

	if(det > -epsilon && det < epsilon)
		return false;

	inv_det = 1.f / det;

	r = ray.origin - triangle.points[0];
	u = dot(r, p) * inv_det;
	
	if(u < 0.f || u > 1.f) 
		return false;

	q = cross(r, edge1);
	v = dot(ray.direction, q) * inv_det;

	if(v < 0 || v+u > 1)
		return false;

	t = dot(edge2, q) * inv_det;

	if(t > epsilon)
	{
		result->t = t;
		result->point = ray.origin + ray.direction * t;
		result->normal = cross(edge1, edge2);
		return true;
	}
	return false;
}

enum quadrant_t 
{
	Q_LEFT = -1, 
	Q_MIDDLE = 0, 
	Q_RIGHT = 1
};

bool _raytrace_aabb_base(struct ray_t ray, float3 min_b_v, float3 max_b_v, struct raytrace_result_t* result)
{
	bool inside = true;
	enum quadrant_t quadrant[3];
	float candidate_plane[3];
	int i;

	float max_t[3];
	int which_plane;

	float min_b[] = { min_b_v.x, min_b_v.y, min_b_v.z };
	float max_b[] = { max_b_v.x, max_b_v.y, max_b_v.z };
	float origin[] = { ray.origin.x, ray.origin.y, ray.origin.z };
	float direction[] = { ray.direction.x, ray.direction.y, ray.direction.z };

	for(i = 0; i<3; ++i)
	{
		if(origin[i] < min_b[i])
		{
			quadrant[i] = Q_LEFT;
			candidate_plane[i] = min_b[i];
			inside = false;
		}
		else if(origin[i] > max_b[i])
		{
			quadrant[i] = Q_RIGHT;
			candidate_plane[i] = max_b[i];
			inside = false;
		}
		else
		{
			quadrant[i] = Q_MIDDLE;
		}
	}

	if(inside)
	{
		result->reason = 1;
		result->t = 0;
		result->point = ray.origin;
		result->normal = (float3)(0,1,0);
		return true;
	}

	for(i = 0; i<3; ++i)
	{
		if(quadrant[i] != Q_MIDDLE && !(direction[i] > -epsilon && direction[i] < epsilon))
			max_t[i] = (candidate_plane[i] -  origin[i]) / direction[i];
		else
			max_t[i] = -1.f;
	}

	int max_plane_idx = 0;
	for(i = 1; i<3; ++i)
		if(max_t[max_plane_idx] < max_t[i])
			max_plane_idx = i;

	if(max_t[max_plane_idx] < 0.f)
	{
		result->reason = 2;
		return false;
	}

	float p[3];
	for(i = 0; i<3; i++)
	{
		if (max_plane_idx != i) 
		{
			float x = origin[i] + max_t[max_plane_idx] * direction[i];
			if (x < min_b[i] || x > max_b[i])
			{
				result->reason = 3;
				return false;
			}
			p[i] = x;
		}
		else
			p[i] = candidate_plane[i];
	}
	result->t     = max_t[max_plane_idx];
	result->point = (float3)(p[0], p[1], p[2]);
	float n[] = { 0, 0, 0 };
	n[max_plane_idx] = quadrant[max_plane_idx];
	result->normal = (float3)(n[0], n[1], n[2]);
	return true;
}

bool raytrace_aacube(struct ray_t ray, struct aacube_t cube, struct raytrace_result_t* result)
{
	return _raytrace_aabb_base(ray, cube.origin, cube.origin + cube.width, result);
}

bool raytrace_aabb(struct ray_t ray, struct aabb_t aabb, struct raytrace_result_t* result)
{
	return _raytrace_aabb_base(ray, aabb.origin, aabb.origin + aabb.size, result);
}

bool raytrace_scene(struct ray_t ray, uint obj_count, __global struct reference_t* obj_references, __global char* obj_data, struct raytrace_result_t* raytrace_result, __global struct reference_t* excluded_obj)
{
	struct raytrace_result_t result;

	struct raytrace_result_t min_result;
	min_result.t = 2e30f;

	__global struct reference_t* curr_ref = obj_references;
	for(int i_obj = 0; i_obj < obj_count; ++i_obj)
	{
		if(curr_ref != excluded_obj)
		{
			bool intersection = false;
			__global char *obj = obj_data + curr_ref->offset;
			switch(curr_ref->type)
			{
				case OBJ_AACUBE:
					intersection = raytrace_aacube(ray, *((struct aacube_t*)obj), &result);
					break;
				case OBJ_AABB:
					intersection = raytrace_aabb(ray, *((struct aabb_t*)obj), &result);
					break;
				case OBJ_BOX:
					intersection = false; // Not implemented
					break;
				case OBJ_SPHERE:
					intersection = raytrace_sphere(ray, *((struct sphere_t*)obj), &result);
					break;
			}
			if(intersection)
				if(min_result.t > result.t)
				{
					min_result = result;
					min_result.object = curr_ref;
				}
		}
		++curr_ref;
	}
	*raytrace_result = min_result;
	return min_result.t < 2e30f;
}

float3 light_directional(struct raytrace_result_t raytrace_result, struct directional_light_t light, 
						 uint obj_count, __global struct reference_t* obj_references, __global char* obj_data)
{
	float3 light_dir = normalize(light.direction.xyz);
	struct ray_t ray = { raytrace_result.point, light_dir };
	struct raytrace_result_t result;

	if(raytrace_scene(ray, obj_count, obj_references, obj_data, &result, raytrace_result.object))
		return (float3)(0.0f);

	float intensity = fmax(dot(light_dir, raytrace_result.normal), 0);
	return light.color.xyz * intensity; 
}

struct __attribute__((packed)) test_data_t
{
	int3 loc;
	float3 start_point;
	float3 direction;
};

#include "voxel.cl"

__kernel void raytrace(image2d_t img, __global struct camera_t* cameras, 
					   __global struct chunk_array_t* chunk_array_p,
					   uint light_count, __global struct reference_t* light_references, __global char* light_data,
					   __global uint* test_data, __global struct voxel_t* voxels)
{
    int x = get_global_id(0);
    int y = get_global_id(1);
    int2 coord = (int2)(x,y);
    int2 framesize = (int2)(get_global_size(0), get_global_size(1));
    
    struct camera_t camera = cameras[0];
	struct chunk_array_t chunk_array = *chunk_array_p;
    
    float2 ratio = convert_float2(coord)/convert_float2(framesize);
    float xpart = camera.bounds.left + ratio.x * (camera.bounds.right  - camera.bounds.left);
    float ypart = camera.bounds.top  + ratio.y * (camera.bounds.bottom - camera.bounds.top);
          
    struct ray_t ray;
    ray.origin    = camera.position.xyz;
    ray.direction = rotate_vector(camera.orientation, normalize((float3)(xpart, camera.warp, -ypart)));
    
    float3 color = {0,0,0};
    struct raytrace_result_t result;
	result.t = 1e20f;

	bool intersection = false;
	intersection = raytrace_chunk_array(ray, chunk_array, &result);

	__global struct reference_t* curr_ref;
	if(intersection)
	{
		curr_ref = light_references;
		for(int i_light = 0; i_light < light_count; ++i_light)
		{
			__global char* lght = light_data + curr_ref->offset;
			switch(curr_ref->type)
			{
				case LIGHT_DIRECTIONAL:
					color += fmax(dot(normalize(((struct directional_light_t*)lght)->direction.xyz), result.normal), 0); 
					//light_directional(result, *((struct directional_light_t*)lght), obj_count, obj_references, obj_data);
					break;
			}

			++curr_ref;
		}
		color *= (float3)((result.loc.z + 4) / 32.f);
		//color = fmod(convert_float3(result.loc), 16) / 16.f;
		//color = convert_float3(result.loc) / 32.f;
	}

    write_imagef(img, (int2)(x,y), (float4)(color, 1.f) );
}

/*
__kernel void raytrace(image2d_t img, __global struct camera_t* cameras, 
					   uint obj_count,   __global struct reference_t* obj_references,   __global char* obj_data, 
					   uint light_count, __global struct reference_t* light_references, __global char* light_data,
					   __global int* test_data)
{
    int x = get_global_id(0);
    int y = get_global_id(1);
    int2 coord = (int2)(x,y);
    int2 framesize = (int2)(get_global_size(0), get_global_size(1));
    
    struct camera_t camera = cameras[0];
    
    float2 ratio = convert_float2(coord)/convert_float2(framesize);
    float xpart = camera.bounds.left + ratio.x * (camera.bounds.right  - camera.bounds.left);
    float ypart = camera.bounds.top  + ratio.y * (camera.bounds.bottom - camera.bounds.top);
          
    struct ray_t ray;
    ray.origin    = camera.position.xyz;
    ray.direction = rotate_vector(camera.orientation, normalize((float3)(xpart, ypart, camera.warp)));
          
    float3 color = {0,0,0};
    struct raytrace_result_t result;

	bool intersection = raytrace_scene(ray, obj_count, obj_references, obj_data, &result, 0);
	
	__global struct reference_t* curr_ref;
	if(intersection)
	{
		curr_ref = light_references;
		for(int i_light = 0; i_light < light_count; ++i_light)
		{
			__global char* lght = light_data + curr_ref->offset;
			switch(curr_ref->type)
			{
				case LIGHT_DIRECTIONAL:
					color += light_directional(result, *((struct directional_light_t*)lght), obj_count, obj_references, obj_data);
					break;
			}

			++curr_ref;
		}
	}

    write_imagef(img, (int2)(x,y), (float4)(color, 1.f) );
}*/