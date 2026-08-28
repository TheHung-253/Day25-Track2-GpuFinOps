# Báo cáo Tối ưu hoá Chi phí GPU (GPU FinOps) - Lab 25

**Họ và tên:** [Điền tên của bạn]
**Lớp/Nhóm:** [Điền thông tin lớp/nhóm]

---

## 1. Baseline vs. Optimized (Tình trạng ban đầu vs. Sau tối ưu)
Sau khi áp dụng toàn diện 4 chiến lược tối ưu hóa, tổng chi phí hàng tháng (Baseline spend) đã giảm mạnh từ **$27,133** xuống chỉ còn **$14,626** (Optimized spend). Tổng số tiền tiết kiệm ước tính đạt **$12,507** (tương đương với mức giảm **46%** tổng ngân sách).

Khi xét riêng khối lượng inference, chi phí quy đổi **$/1M-token** đã chứng kiến mức giảm ấn tượng từ **$6.488** xuống chỉ còn **$1.126**, tương ứng với hiệu quả tiết kiệm **82.6%**. Thành quả này chủ yếu đến từ việc kết hợp định tuyến mô hình (cascade routing), sử dụng bộ nhớ đệm (prompt caching), và xử lý gộp lô (batch API).

## 2. Phân tích từng đòn bẩy tiết kiệm
Dựa trên báo cáo Waterfall, dưới đây là mức độ đóng góp của từng đòn bẩy:
- **Purchasing (spot/reserved):** Đây là đòn bẩy đóng góp nhiều nhất với mức tiết kiệm lên tới **$10,040**. Việc chuyển các job có khả năng gián đoạn sang sử dụng Spot (ví dụ: `job-train-llm`) mang lại lợi ích kinh tế vô cùng lớn mà không làm suy giảm chất lượng đầu ra.
- **Inference (cascade/cache/batch):** Đóng góp **$1,212** vào khoản tiết kiệm hàng tháng. Dù số tiền tuyệt đối không quá cao như Purchasing, nhưng tỷ suất tiết kiệm trên mỗi token lại cực kỳ lớn (giảm 82.6%).
- **Right-size util-lies:** Tiết kiệm **$655** thông qua việc phát hiện và hạ cấp các GPU báo cáo "ảo" mức độ sử dụng (GPU-Util cao nhưng hiệu suất MFU thực tế thấp).
- **Kill idle GPUs:** Tránh lãng phí **$600** nhờ việc tắt các GPU hoàn toàn nhàn rỗi (utilization < 10%).

## 3. GPU-Util Lie (Hiện tượng báo cáo ảo mức độ sử dụng GPU)
Qua phân tích telemetry, hệ thống đã phát hiện ra các GPU gặp tình trạng "GPU-Util Lie" (báo cáo GPU-Util > 90% nhưng hiệu năng sinh ra MFU < 30%):
- **gpu-h100-4**: Mức độ sử dụng (utilization) 98.2% nhưng hiệu quả tính toán (MFU) chỉ đạt 19.4%
- **gpu-a10g-1**: Mức độ sử dụng (utilization) 96.9% nhưng hiệu quả tính toán (MFU) chỉ đạt 26.8%

**Tác động tài chính**: Các GPU này bề ngoài có vẻ đang chạy "hết công suất", nhưng thực chất lại bị nghẽn băng thông (memory-bound) hoặc đang trong trạng thái chờ I/O. Nếu công ty tiếp tục trả tiền cho nguyên một chiếc H100 với giá đắt đỏ nhưng chỉ khai thác được 1/5 sức mạnh tính toán, đó là một sự lãng phí hạ tầng nghiêm trọng.

## 4. Phần mở rộng "Your Turn" đã triển khai
Trong bài lab này, em đã chọn và triển khai 2 phần mở rộng: **Extension 4 (Ngân sách Reasoning)** và **Extension 5 (Carbon-aware Scheduling)**.

### Extension 4: Ngân sách Reasoning
- **Mô tả:** Thêm logic vào hàm tính toán để tách biệt lượng token, chi phí tiền mặt và năng lượng tiêu thụ của các request yêu cầu suy luận phức tạp (`is_reasoning=1`).
- **Kết quả đo lường:** Các traffic reasoning chỉ chiếm **16.5%** tổng lượng token và **16.5%** ngân sách tiền mặt. Tuy nhiên, về mặt năng lượng, Reasoning tiêu thụ tới **29,787.7 Wh**, gấp hơn 15 lần so với Non-reasoning (chỉ **1,887.6 Wh**).
- **Insight quan trọng:** Chi phí tài chính của reasoning có thể bị "ẩn lấp" do giá token không đổi, nhưng hệ lụy về chi phí vận hành hạ tầng điện và phát thải môi trường là cực kỳ lớn. Do đó, cần kiểm soát gắt gao tỷ lệ gọi vào mô hình reasoning.

### Extension 5: Carbon-aware Scheduling
- **Mô tả:** Cập nhật script purchasing để điều phối các job có khả năng gián đoạn (interruptible) theo tiêu chí giảm lượng khí thải carbon. So sánh lượng carbon phát thải khi chạy job ở `us-east-1` so với region ưu tiên năng lượng xanh `europe-north1`.
- **Kết quả đo lường:** Nếu chạy ở `us-east-1`, lượng phát thải lên tới **1,606,260 gCO2e**. Nếu điều phối tự động sang `europe-north1`, phát thải giảm xuống còn **126,810 gCO2e**. Tổng lượng tiết kiệm đạt **1,479,450 gCO2e** (giảm **92.1%**).
- **Insight quan trọng:** Không chỉ tối ưu chi phí, việc lựa chọn trung tâm dữ liệu (region) một cách thông minh cho các job dạng batch có thể giúp startup đạt được mục tiêu Net-Zero dễ dàng mà không phát sinh thêm chi phí đám mây.

## 5. Khuyến nghị cho NimbusAI
Dưới vai trò là một FinOps Engineer, 3 hành động em sẽ ưu tiên triển khai ngay lập tức là:
1. **Thiết lập chính sách Spot-by-default cho Batch & Training**: Buộc (force) các job có khả năng gián đoạn sử dụng Spot instance thay vì On-demand. Đây là đòn bẩy mang lại tỷ suất hoàn vốn (ROI) lớn và nhanh nhất cho dòng tiền của startup.
2. **Triển khai Cổng định tuyến API (Routing Gateway) có hạn mức Reasoning**: Xây dựng proxy để lọc các tác vụ đơn giản và tự động chuyển về mô hình thường, giới hạn trần lượng traffic gọi vào mô hình reasoning để ngăn chặn tình trạng quá tải điện năng.
3. **Dịch chuyển vị trí địa lý cho Job không yêu cầu thời gian thực**: Tự động hóa việc deploy các job training dài hạn vào region `europe-north1` (vùng dùng thủy điện/năng lượng xanh) nhằm cắt giảm tới 90% lượng carbon footprint, nâng cao giá trị thương hiệu phát triển bền vững của công ty.
