import math


def nearest_point_searcher(user_list, check_list):
    fi1_user_point = user_list[0]
    lamb1_user_point = user_list[1]
    fi2_check_point = check_list[0]
    lamb2_check_point = check_list[1]
    delta_lamb = lamb1_user_point - lamb2_check_point
    sin_counter = math.sin(fi1_user_point) * math.sin(fi2_check_point)
    cos_counter = math.cos(fi1_user_point) * math.cos(fi2_check_point) * delta_lamb
    delta_corner = math.acos(sin_counter + cos_counter)
    return delta_corner
