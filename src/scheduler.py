from datetime import datetime, timedelta, time

# サロンの基本設定
SLOT_UNIT_MINUTES = 30 # 30分単位
OPEN_TIME = time(9, 0) # 開店 9:00
CLOSE_TIME = time(20, 0) # 閉店 20:00

def generate_slots(target_date):
    """
    指定された日付における30分刻みの予約枠候補を生成する
    """
    slots = []
    current_dt = datetime.combine(target_date, OPEN_TIME)
    close_dt = datetime.combine(target_date, CLOSE_TIME)

    while current_dt + timedelta(minutes=SLOT_UNIT_MINUTES) <= close_dt:
        start_time = current_dt
        end_time = current_dt + timedelta(minutes=SLOT_UNIT_MINUTES)
        
        slots.append({
            "start": start_time,
            "end": end_time,
            "display": f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        })
        
        # 次の枠は現在の終了時間から開始
        current_dt = end_time

    return slots

def check_availability(required_slots, target_date, existing_events):
    """
    空き状況判定エンジン
    required_slots: メニューに必要なスロット数（例：カットなら1、カラーなら2）
    existing_events: Larkカレンダーから取得した既存の予定リスト [{'start': dt, 'end': dt}, ...]
    """
    all_slots = generate_slots(target_date)
    available_start_times = []

    # 連続したスロットが必要な場合を考慮して探索
    # 例: 2スロット必要なら、Slot[i]とSlot[i+1]が両方空いている必要がある
    
    for i in range(len(all_slots) - required_slots + 1):
        # 連続案候補のスロット群
        candidate_slots = all_slots[i : i + required_slots]
        
        # 候補全体の開始と終了
        candidate_start = candidate_slots[0]['start']
        candidate_end = candidate_slots[-1]['end']
        
        is_conflict = False
        for event in existing_events:
            # 衝突判定: (StartA < EndB) and (EndA > StartB)
            if (candidate_start < event['end']) and (candidate_end > event['start']):
                is_conflict = True
                break
        
        if not is_conflict:
            available_start_times.append({
                "start_time": candidate_start,
                "end_time": candidate_end,
                "label": f"{candidate_start.strftime('%H:%M')}開始 (〜{candidate_end.strftime('%H:%M')})"
            })
            
    return available_start_times
