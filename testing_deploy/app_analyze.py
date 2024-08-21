from gpt_intergrate import generateAnalysis

test = generateAnalysis("T",3)
# print(test.analyze_progress())
# print(test.analyze_deep())
# print(test.detail_plan_and_timeline())
print(test.chap_plan())


# bố trí lại threshold json base line thành
# 1 file csv gồm các cột : Chương / Độ khó / Thời điểm làm test / Accuracy
# ban đầu AI sẽ recommend ra 1 threshold gọi là baseline 
# sau đó ta sẽ dùng machine learning để predict ra threshold mới dựa trên dữ liệu cũ
# à việc predict cho baseline sẽ dựa vào cả phân bố các type câu hỏi của bài test

