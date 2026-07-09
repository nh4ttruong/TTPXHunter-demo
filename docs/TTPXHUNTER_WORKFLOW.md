# Workflow tổng quát của TTPXHunter

Tài liệu này vẽ lại workflow tổng quát của TTPXHunter dựa trên paper
["TTPXHunter: Actionable Threat Intelligence Extraction as TTPs from Finished Cyber Threat Reports"](https://arxiv.org/html/2403.03267v3)
và source code reproduce trong repo này.

Ý chính: TTPXHunter chuyển báo cáo threat intelligence dạng văn bản tự do thành
danh sách kỹ thuật MITRE ATT&CK bằng cách tách báo cáo thành câu, phân loại từng
câu bằng mô hình transformer chuyên biệt cho an ninh mạng, lọc các dự đoán thiếu
tin cậy, rồi gom kết quả ở mức toàn bộ báo cáo.

```mermaid
flowchart TD
    A["MITRE ATT&CK knowledge base<br/>+ dữ liệu sentence-TTP từ TTPHunter"] --> B["Tiền xử lý dữ liệu huấn luyện"]
    B --> C["Tăng cường dữ liệu theo ngữ cảnh"]
    C --> C1["Mask từng từ trong câu"]
    C1 --> C2["SecureBERT MLM dự đoán từ thay thế"]
    C2 --> C3["Tạo câu mới"]
    C3 --> C4["Lọc bằng cosine similarity<br/>để giữ nguyên ngữ nghĩa"]
    C4 --> D["Augmented sentence-TTP dataset"]

    D --> E["Fine-tune mô hình"]
    E --> E1["SecureBERT tokenizer"]
    E1 --> E2["SecureBERT encoder"]
    E2 --> E3["Linear classifier"]
    E3 --> F["Mô hình TTPXHunter đã huấn luyện"]

    G["Finished cyber threat report"] --> H["Làm sạch văn bản"]
    H --> I["Tách báo cáo thành từng câu"]
    I --> J["Tokenize từng câu"]
    J --> F

    F --> K["Dự đoán TTP cho từng câu"]
    K --> L["Tính confidence score"]
    L --> M{"Confidence > threshold?"}
    M -- "Không" --> N["Loại câu không liên quan"]
    M -- "Có" --> O["Giữ TTP dự đoán"]

    O --> P["Map LABEL_n sang ATT&CK ID"]
    P --> Q["Map ATT&CK ID sang tên technique"]
    Q --> R["Gộp các TTP duy nhất<br/>ở mức toàn bộ report"]
    R --> S["Kết quả cuối:<br/>danh sách MITRE ATT&CK TTPs"]

    S --> T["Xuất kết quả:<br/>CLI / JSON / STIX"]
    S --> U["Đánh giá benchmark:<br/>so sánh predicted vs expected,<br/>tính precision, recall, F1"]

    classDef data fill:#e8f5e9,stroke:#2e7d32,color:#111;
    classDef train fill:#e3f2fd,stroke:#1565c0,color:#111;
    classDef infer fill:#fff8e1,stroke:#f57f17,color:#111;
    classDef decision fill:#fff3e0,stroke:#ef6c00,color:#111;
    classDef output fill:#fce4ec,stroke:#ad1457,color:#111;

    class A,D,G data;
    class B,C,C1,C2,C3,C4,E,E1,E2,E3,F train;
    class H,I,J,K,L,O,P,Q,R infer;
    class M decision;
    class S,T,U output;
```

## Diễn giải ngắn

| Giai đoạn | Vai trò |
| --- | --- |
| Dữ liệu nền | Lấy tri thức từ MITRE ATT&CK và dữ liệu sentence-TTP của TTPHunter. |
| Tăng cường dữ liệu | Dùng SecureBERT dạng Masked Language Model để tạo thêm câu cho các lớp TTP ít dữ liệu, sau đó lọc bằng cosine similarity để tránh lệch nghĩa. |
| Huấn luyện | Fine-tune SecureBERT kết hợp linear classifier để ánh xạ một câu sang một lớp TTP. |
| Suy luận | Nhận threat report, làm sạch văn bản, tách câu, tokenize, rồi đưa từng câu qua mô hình. |
| Lọc câu liên quan | Chỉ giữ dự đoán có confidence vượt threshold, giúp loại các câu không mô tả hành vi tấn công. |
| Gom kết quả | Chuyển nhãn mô hình sang ATT&CK ID, map sang tên technique, loại trùng và trả về danh sách TTP của toàn bộ báo cáo. |
| Đánh giá | Với benchmark như CISA, so sánh TTP dự đoán với nhãn kỳ vọng để tính precision, recall và F1. |

## Note

- Dùng model đã huấn luyện sẵn `nanda-rani/TTPXHunter`;
- Tách câu bằng NLTK
- Lọc dự đoán bằng threshold `0.644`;
- Map `LABEL_n` sang MITRE ATT&CK ID bằng `model_artifacts/label_dict.pkl`;
- Map ATT&CK ID sang tên technique bằng `model_artifacts/ttp_id_name.pkl`;
- Xuất kết quả qua CLI/JSON và có thêm workflow benchmark trên CISA.