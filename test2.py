def bubble_sort(arr):
    """
    冒泡排序算法实现
    通过重复遍历列表，比较相邻元素并交换位置，将较大的元素逐渐"冒泡"到列表末尾
    """
    # 创建列表的副本，避免修改原列表
    nums = arr.copy()
    n = len(nums)
    
    # 外层循环控制遍历次数
    for i in range(n):
        # 标记本轮是否发生交换，用于优化
        swapped = False
        
        # 内层循环进行相邻元素比较
        # 每轮结束后，最大的元素已经沉底，所以范围可以缩小
        for j in range(0, n - i - 1):
            # 如果前一个元素大于后一个元素，则交换
            if nums[j] > nums[j + 1]:
                nums[j], nums[j + 1] = nums[j + 1], nums[j]
                swapped = True
        
        # 如果本轮没有发生交换，说明列表已经有序，提前退出
        if not swapped:
            break
    
    return nums


# 测试代码
if __name__ == "__main__":
    # 测试数据
    test_arr = [64, 34, 25, 12, 22, 11, 90]
    print(f"原始数组: {test_arr}")
    print(f"排序后: {bubble_sort(test_arr)}")
