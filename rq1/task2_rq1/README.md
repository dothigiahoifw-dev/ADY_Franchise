# ADY_PRJ RQ1 — Task 2 (gói bàn giao, bản hoàn thiện)

Trạng thái: PHƯƠNG ÁN KHUYẾN NGHỊ, chưa nhóm duyệt. Không model nào được train; test chưa được chấm.

## Quy tắc phạm vi (bắt buộc)
- **Task 3 hiện tại chỉ chạy trên dev** (725 dòng, fold 1–4). **Chưa chấm test.**
- **Không mở `data/rq1_inputs_test_LOCKED.csv`.** Chấm test là task riêng sau khi khóa cấu hình (hash) và nhóm đồng ý.
- **Bước đầu tiên của Task 3: `python task3_preflight.py`.** Nếu in FAIL (mã thoát 1) thì dừng, không chạy tiếp.

## Đọc theo thứ tự
1. `TASK2_RQ1_REPORT.md` — thiết kế đầy đủ (mục 12: đầu vào và cổng kiểm tra).
2. `design_config_rq1.json`, `experiment_plan_rq1.csv`, `feature_registry_rq1.csv`.
3. Đầu vào Task 3 (tra theo `transition_id`): `data/rq1_inputs_dev.csv`, `data/baseline_v2_dev_preds_wide.csv`, `data/split_assignment.csv`.
4. Đối chiếu: `data/sample_rq1_membership.csv`, `data/sample_funnel.csv`, `data/exclusions.csv`, `data/baseline_v2_reference_metrics.csv`, `data/verified_numbers.json`, `data/checks_source.csv`.
5. Hash: `manifest_outputs.csv` (file bàn giao), `data/manifest_sources.csv` (file nguồn).

## Chạy lại từ nguồn (không bắt buộc cho Task 3)
```
python verify_task2.py --project <thư mục có pairs_audit.csv, analysis_master_films.csv> --split <thư mục có rq1_split_v2.csv, rq1_baseline_dev_preds_v2.csv> --out data
python build_design_files.py data
python task3_preflight.py
```
`verify_task2.py` chạy cổng kiểm tra trước; FAIL thì dừng và không ghi output nào khác.

## Task 3 (chỉ dev)
1. `python task3_preflight.py` phải PASS.
2. Dựng pipeline OLS theo fold từ `rq1_inputs_dev.csv` (bước tiền xử lý: mục 7 báo cáo; `assert` giá trị hợp lệ).
3. Chạy E0 và xác nhận khớp `pred_reg_log_open_prev` theo `transition_id`.
4. Đồ thị phần dư theo feature của E4 trên dev; nếu cần, tối đa một thay đổi biểu diễn mỗi feature (ghi nhật ký có thời điểm) trước khi so MAE.
5. Chạy E1–E4; áp quy tắc chọn (mục 8); báo cổng kết luận so với từng baseline.
6. Chạy S1, S2 theo định nghĩa trong `experiment_plan_rq1.csv`: S1 so run chính và run S1 trên cùng 719 dòng không cờ (6 dòng có cờ báo riêng); S2 đánh giá trên cùng 725 dòng dev. Cả hai: baseline fit lại cùng cách, ghép cặp theo `transition_id`.
7. Phân tích lỗi theo tầng/bucket/gap/vị trí/thập niên; liệt kê 31 dòng dev `≥ 1M` có `open_curr < 1M` và các |Y| > 3 theo `transition_id`.
8. Khóa cấu hình (hash) và dừng. **Không chấm test trong Task 3.** E5–E7 chỉ sau khi khóa, và chỉ nếu đã có file policy.

## File còn thiếu (để đóng các điểm OPEN)
`analysis_master_transitions.csv`, `transitions_model_rq1.csv`, `rq1_feature_policy.csv`, `feature_registry_transitions.csv`, báo cáo DP v3.3.
