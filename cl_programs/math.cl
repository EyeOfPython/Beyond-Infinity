

int quadratic_roots(float a, float b, float c, float *x1, float *x2)
{
    float det = b*b - 4*a*c;
    if(det < 0)
    {
		*x1 = *x2 = 0;
		return 0;
    }
    det = sqrt(det);
    *x1 = (-b + det) / (2*a);
    *x2 = (-b - det) / (2*a);
    if(*x1 > *x2)
    {
		det = *x1;
		*x1 = *x2;
		*x2 = det;
    }
    return 2;
}

float4 mult_quat(float4 q1, float4 q2)
{
	return (float4)(
		-q1.y*q2.y - q1.z*q2.z - q1.w*q2.w + q1.x*q2.x,
		 q1.y*q2.x + q1.z*q2.w - q1.w*q2.z + q1.x*q2.y,
		-q1.y*q2.w + q1.z*q2.x + q1.w*q2.y + q1.x*q2.z,
		 q1.y*q2.z - q1.z*q2.y + q1.w*q2.x + q1.x*q2.w
	);
}

float3 rotate_vector( float4 quat, float3 vec )
{
	return vec + 2.0f * cross( cross( vec, quat.yzw ) + quat.x * vec, quat.yzw );
}