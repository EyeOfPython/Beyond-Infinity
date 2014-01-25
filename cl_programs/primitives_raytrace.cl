
float3 sphere_get_normal_at(sphere_t sphere, float3 pos)
{
    return normalize( pos - sphere.center );
}

bool raytrace_sphere(ray_t ray,  sphere_t sphere,  raytrace_result_t* result)
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

bool raytrace_triangle( ray_t ray,  triangle_t triangle,  raytrace_result_t* result)
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

bool _raytrace_aabb_base( ray_t ray, float3 min_b_v, float3 max_b_v,  raytrace_result_t* result)
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

bool raytrace_aacube( ray_t ray,  aacube_t cube,  raytrace_result_t* result)
{
	return _raytrace_aabb_base(ray, cube.origin, cube.origin + cube.width, result);
}

bool raytrace_aabb( ray_t ray,  aabb_t aabb,  raytrace_result_t* result)
{
	return _raytrace_aabb_base(ray, aabb.origin, aabb.origin + aabb.size, result);
}