def format_duration(seconds):
    """초를 '시, 분, 초' 형태로 변환하는 함수 (소수점 둘째 자리까지)"""
    if seconds < 60:
        return f"{seconds:.2f}초"

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        return f"{int(hours)}시간 {int(minutes)}분 {seconds:.2f}초"
    else:
        return f"{int(minutes)}분 {seconds:.2f}초"
