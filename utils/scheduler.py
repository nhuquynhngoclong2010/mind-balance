"""
AI Scheduler - Tạo lịch thông minh CHỐNG BURN OUT
Tích hợp 8 frameworks tâm lý học
"""

from datetime import datetime, timedelta

def create_daily_schedule(tasks_with_meta, fixed_schedule, work_start="06:00", work_end="22:00", 
                         energy_level=5, today_framework=""):
    """
    Tạo lịch thông minh với logic chống burn out
    
    Args:
        tasks_with_meta: List[dict] - Tasks với metadata
        fixed_schedule: List[dict] - Lịch cố định
        work_start: str - Giờ thức dậy
        work_end: str - Giờ đi ngủ
        energy_level: int - Năng lượng (1-10)
        today_framework: str - Framework hôm nay
    
    Returns:
        dict: Lịch đầy đủ với cảnh báo + gợi ý
    """
    
    # Chuẩn hóa key names (database trả về 'task_name' nhưng code cần 'name')
    for task in tasks_with_meta:
        if 'task_name' in task and 'name' not in task:
            task['name'] = task['task_name']
    
    # Parse time
    day_start = datetime.strptime(work_start, "%H:%M")
    day_end = datetime.strptime(work_end, "%H:%M")
    
    # Parse fixed schedule
    fixed_blocks = []
    for block in fixed_schedule:
        fixed_blocks.append({
            'start': datetime.strptime(block['start'], "%H:%M"),
            'end': datetime.strptime(block['end'], "%H:%M"),
            'name': block['name'],
            'type': 'Cố định'
        })
    
    fixed_blocks.sort(key=lambda x: x['start'])
    
    # Tìm khoảng trống
    free_slots = []
    current_time = day_start
    
    for block in fixed_blocks:
        if current_time < block['start']:
            free_duration = int((block['start'] - current_time).total_seconds() / 60)
            if free_duration >= 30:
                free_slots.append({
                    'start': current_time,
                    'end': block['start'],
                    'duration': free_duration
                })
        current_time = max(current_time, block['end'])
    
    if current_time < day_end:
        free_duration = int((day_end - current_time).total_seconds() / 60)
        if free_duration >= 30:
            free_slots.append({
                'start': current_time,
                'end': day_end,
                'duration': free_duration
            })
    
    total_free_minutes = sum([slot['duration'] for slot in free_slots])
    total_task_time = sum([t['estimated_time'] for t in tasks_with_meta])
    
    # LOGIC CHỐNG BURN OUT
    warnings = []
    suggestions = []
    
    # Chỉ nên làm 70% thời gian rảnh
    effective_free_time = int(total_free_minutes * 0.7)
    
    # Điều chỉnh theo năng lượng
    if energy_level <= 3:
        max_work_time = int(effective_free_time * 0.6)
        warnings.append(f"⚠️ Năng lượng thấp ({energy_level}/10) - Chỉ nên làm {max_work_time//60}h{max_work_time%60}'")
    elif energy_level <= 6:
        max_work_time = int(effective_free_time * 0.8)
    else:
        max_work_time = effective_free_time
    
    # Phát hiện overload
    if total_task_time > max_work_time:
        overload = total_task_time - max_work_time
        warnings.append(f"🔥 CẢNH BÁO KIỆT SỨC: {total_task_time//60}h{total_task_time%60}' công việc vs {max_work_time//60}h{max_work_time%60}' khả dụng")
        warnings.append(f"⚠️ Cần giảm {overload//60}h{overload%60}' để tránh burn out!")
    
    # Phân loại tasks
    deep_work = [t for t in tasks_with_meta if t['task_type'] == 'Học sâu']
    meetings = [t for t in tasks_with_meta if t['task_type'] == 'Họp/Gặp mặt']
    shallow = [t for t in tasks_with_meta if t['task_type'] == 'Công việc nhẹ']
    
    priority_map = {'Cao': 1, 'Trung bình': 2, 'Thấp': 3}
    deep_work.sort(key=lambda x: priority_map.get(x['priority'], 99))
    shallow.sort(key=lambda x: priority_map.get(x['priority'], 99))
    
    # FRAMEWORK INSIGHTS
    insights = get_framework_insights(today_framework, tasks_with_meta, energy_level)
    suggestions.extend(insights)
    
    # TẠO LỊCH
    schedule = []
    scheduled_tasks = []
    worked_minutes = 0
    last_break_time = None
    
    # Thêm fixed schedule
    for block in fixed_blocks:
        schedule.append({
            'start': block['start'].strftime("%H:%M"),
            'end': block['end'].strftime("%H:%M"),
            'task': block['name'],
            'type': 'Cố định',
            'priority': 'Hệ thống',
            'color': '#9CA3AF'
        })
    
    # Xếp tasks vào free slots
    for slot in free_slots:
        slot_start = slot['start']
        slot_remaining = slot['duration']
        current_time = slot_start
        hour = slot_start.hour
        
        # Xác định slot type
        if 6 <= hour < 12:
            slot_type = 'Sáng'
        elif 12 <= hour < 14:
            slot_type = 'Trưa'
        elif 14 <= hour < 18:
            slot_type = 'Chiều'
        else:
            slot_type = 'Tối'
        
        # Slot buổi trưa - ưu tiên ăn + nghỉ
        if slot_type == 'Trưa':
            lunch_duration = min(45, slot_remaining)
            lunch_end = current_time + timedelta(minutes=lunch_duration)
            schedule.append({
                'start': current_time.strftime("%H:%M"),
                'end': lunch_end.strftime("%H:%M"),
                'task': '🍱 Ăn trưa + nghỉ ngơi',
                'type': 'Nghỉ',
                'priority': 'Hệ thống',
                'color': '#10B981'
            })
            current_time = lunch_end
            slot_remaining -= lunch_duration
            
            # Shallow work nếu còn thời gian
            if slot_remaining >= 30:
                for task in shallow[:]:
                    if worked_minutes >= max_work_time:
                        break
                    
                    task_duration = min(task['estimated_time'], slot_remaining, max_work_time - worked_minutes)
                    if task_duration < 15:
                        continue
                    
                    task_end = current_time + timedelta(minutes=task_duration)
                    schedule.append({
                        'start': current_time.strftime("%H:%M"),
                        'end': task_end.strftime("%H:%M"),
                        'task': task['name'],
                        'type': task['task_type'],
                        'priority': task['priority'],
                        'color': get_color_by_priority(task['priority'])
                    })
                    
                    current_time = task_end
                    worked_minutes += task_duration
                    slot_remaining -= task_duration
                    scheduled_tasks.append(task['name'])
                    
                    if task_duration >= task['estimated_time']:
                        shallow.remove(task)
                    else:
                        task['estimated_time'] -= task_duration
                    break
        
        # Slot buổi sáng - Deep work (năng lượng cao)
        elif slot_type == 'Sáng':
            for task in deep_work[:]:
                if worked_minutes >= max_work_time or slot_remaining < 20:
                    break
                
                task_duration = min(task['estimated_time'], slot_remaining, max_work_time - worked_minutes, 90)
                if task_duration < 20:
                    continue
                
                task_end = current_time + timedelta(minutes=task_duration)
                schedule.append({
                    'start': current_time.strftime("%H:%M"),
                    'end': task_end.strftime("%H:%M"),
                    'task': task['name'],
                    'type': task['task_type'],
                    'priority': task['priority'],
                    'color': get_color_by_priority(task['priority'])
                })
                
                current_time = task_end
                worked_minutes += task_duration
                slot_remaining -= task_duration
                scheduled_tasks.append(task['name'])
                
                if task_duration >= task['estimated_time']:
                    deep_work.remove(task)
                else:
                    task['estimated_time'] -= task_duration
                
                # Auto break sau 60+ phút
                if task_duration >= 60 and slot_remaining >= 10:
                    break_end = current_time + timedelta(minutes=10)
                    schedule.append({
                        'start': current_time.strftime("%H:%M"),
                        'end': break_end.strftime("%H:%M"),
                        'task': '☕ Nghỉ 10 phút',
                        'type': 'Nghỉ',
                        'priority': 'Hệ thống',
                        'color': '#10B981'
                    })
                    current_time = break_end
                    slot_remaining -= 10
                    last_break_time = current_time
                break
        
        # Slot chiều/tối - Mix
        else:
            # Meetings trước
            for task in meetings[:]:
                if worked_minutes >= max_work_time or slot_remaining < task['estimated_time']:
                    continue
                
                task_end = current_time + timedelta(minutes=task['estimated_time'])
                schedule.append({
                    'start': current_time.strftime("%H:%M"),
                    'end': task_end.strftime("%H:%M"),
                    'task': task['name'],
                    'type': 'Họp/Gặp mặt',
                    'priority': task['priority'],
                    'color': '#8B5CF6'
                })
                
                current_time = task_end
                worked_minutes += task['estimated_time']
                slot_remaining -= task['estimated_time']
                scheduled_tasks.append(task['name'])
                meetings.remove(task)
            
            # Shallow work
            for task in shallow[:]:
                if worked_minutes >= max_work_time or slot_remaining < 15:
                    break
                
                task_duration = min(task['estimated_time'], slot_remaining, max_work_time - worked_minutes)
                if task_duration < 15:
                    continue
                
                task_end = current_time + timedelta(minutes=task_duration)
                schedule.append({
                    'start': current_time.strftime("%H:%M"),
                    'end': task_end.strftime("%H:%M"),
                    'task': task['name'],
                    'type': 'Công việc nhẹ',
                    'priority': task['priority'],
                    'color': get_color_by_priority(task['priority'])
                })
                
                current_time = task_end
                worked_minutes += task_duration
                slot_remaining -= task_duration
                scheduled_tasks.append(task['name'])
                
                if task_duration >= task['estimated_time']:
                    shallow.remove(task)
                else:
                    task['estimated_time'] -= task_duration
                
                # Check break
                if last_break_time and (current_time - last_break_time).total_seconds() >= 90*60:
                    if slot_remaining >= 10:
                        break_end = current_time + timedelta(minutes=10)
                        schedule.append({
                            'start': current_time.strftime("%H:%M"),
                            'end': break_end.strftime("%H:%M"),
                            'task': '☕ Nghỉ 10 phút',
                            'type': 'Nghỉ',
                            'priority': 'Hệ thống',
                            'color': '#10B981'
                        })
                        current_time = break_end
                        slot_remaining -= 10
                        last_break_time = current_time
    
    # Tasks chưa xếp được
    unscheduled = []
    for task in deep_work + meetings + shallow:
        unscheduled.append(task['name'])
    
    if len(unscheduled) > 0:
        warnings.append(f"⚠️ Không xếp được {len(unscheduled)} công việc: {', '.join(unscheduled)}")
        
        low_priority = [t for t in tasks_with_meta if t['name'] in unscheduled and t['priority'] == 'Thấp']
        if len(low_priority) > 0:
            suggestions.append(f"💡 Có thể nhờ bạn giúp: {', '.join([t['name'] for t in low_priority])}")
        
        medium_priority = [t for t in tasks_with_meta if t['name'] in unscheduled and t['priority'] == 'Trung bình']
        if len(medium_priority) > 0:
            suggestions.append(f"💡 Có thể dời sang mai: {', '.join([t['name'] for t in medium_priority])}")
    
    # Sắp xếp schedule theo thời gian
    schedule.sort(key=lambda x: datetime.strptime(x['start'], "%H:%M"))
    
    # Stats
    stats = {
        'total_tasks': len(tasks_with_meta),
        'scheduled_tasks': len(scheduled_tasks),
        'unscheduled_tasks': len(unscheduled),
        'actual_work_time': worked_minutes,
        'breaks_count': len([s for s in schedule if s['type'] == 'Nghỉ'])
    }
    
    return {
        'schedule': schedule,
        'warnings': warnings,
        'suggestions': suggestions,
        'stats': stats
    }


def get_framework_insights(framework_name, tasks, energy_level):
    """Framework-specific insights (Tiếng Việt)"""
    insights = []
    
    if "Eisenhower" in framework_name or "Ưu tiên" in framework_name:
        high = len([t for t in tasks if t['priority'] == 'Cao'])
        if high > 3:
            insights.append(f"📘 Eisenhower: {high} công việc ưu tiên cao - Có việc nào chỉ 'gấp' nhưng không thực sự 'quan trọng'?")
    
    elif "Delegation" in framework_name or "Giao việc" in framework_name:
        shallow = len([t for t in tasks if t['task_type'] == 'Công việc nhẹ'])
        if shallow > 2:
            insights.append(f"🤝 Giao việc: {shallow} công việc nhẹ - Bạn bè có thể giúp không?")
    
    elif "Ultradian" in framework_name or "Năng lượng" in framework_name:
        deep_time = sum([t['estimated_time'] for t in tasks if t['task_type'] == 'Học sâu'])
        if energy_level <= 5 and deep_time > 120:
            insights.append(f"⚡ Chu kỳ năng lượng: Năng lượng {energy_level}/10 với {deep_time//60}h học sâu - Nên chia nhỏ!")
    
    elif "Recovery" in framework_name or "Chủ nhật" in framework_name:
        if len(tasks) > 3:
            insights.append(f"😴 Phục hồi: Ngày nghỉ mà {len(tasks)} công việc - Thực sự CẦN làm hôm nay?")
    
    return insights


def get_color_by_priority(priority):
    """Màu sắc theo ưu tiên"""
    colors = {
        'Cao': '#EF4444',           # Đỏ
        'Trung bình': '#F59E0B',    # Vàng
        'Thấp': '#3B82F6'           # Xanh
    }
    return colors.get(priority, '#6B7280')