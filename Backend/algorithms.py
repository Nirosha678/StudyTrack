
from typing import List, Dict, Any


def insertion_sort_by_field(students: List[Dict[str, Any]], field: str) -> List[Dict[str, Any]]:
    
    n = len(students)
    for i in range(1, n):
        key = students[i]
        key_value = key[field]
        j = i - 1
        # Shift every element greater than key_value one position to the right
        while j >= 0 and students[j][field] > key_value:
            students[j + 1] = students[j]
            j -= 1
        # The gap at j + 1 is now key's correct position
        students[j + 1] = key
    return students


def binary_search_by_name(sorted_by_name_list: List[Dict[str, Any]], name: str):
  
    low = 0
    high = len(sorted_by_name_list) - 1

    while low <= high:
        mid = low + (high - low) // 2
        mid_name = sorted_by_name_list[mid]["name"]

        if mid_name == name:
            return sorted_by_name_list[mid]
        elif mid_name < name:
            low = mid + 1
        else:
            high = mid - 1

    return -1


def format_roster_report(students: List[Dict[str, Any]]) -> str:
    
    lines = []
    for student in students:
        line = f"[Age {student['age']}] {student['name']} <{student['email']}>"
        lines.append(line)
    return "\n".join(lines)


def count_students_meeting_min_age(students: List[Dict[str, Any]], min_age: int) -> int:
    
    count = 0
    for student in students:
        if student["age"] >= min_age:
            count += 1
    return count
