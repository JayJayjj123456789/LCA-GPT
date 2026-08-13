# ภาคผนวก

## ภาคผนวก ก: สมการทางคณิตศาสตร์โดยละเอียด

### ก.1 Heijungs & Suh LCA Framework

#### ระบบสมการพื้นฐาน

สมมติระบบเศรษฐกิจมี n กระบวนการผลิต แต่ละกระบวนการผลิตผลผลิต output และใช้ input จากกระบวนการอื่น

**Technology Matrix A ∈ ℝⁿˣⁿ:**

```
A = [a₁₁  a₁₂  ...  a₁ₙ]
    [a₂₁  a₂₂  ...  a₂ₙ]
    [...  ...  ...  ...]
    [aₙ₁  aₙ₂  ...  aₙₙ]
```

โดย:
- `aᵢⱼ` = ปริมาณผลผลิตของกระบวนการ i ที่ต้องใช้เพื่อผลิต 1 หน่วยของกระบวนการ j
- `aᵢᵢ` = 1 (กระบวนการผลิตตัวเอง)
- `aᵢⱼ` < 0 เมื่อ i ≠ j (input จากกระบวนการอื่น)

**ตัวอย่าง:**
```
A = [1.0  -0.5   0.0]    กระบวนการ 1 (Raw Material)
    [0.0   1.0  -0.3]    กระบวนการ 2 (Manufacturing)
    [0.0   0.0   1.0]    กระบวนการ 3 (Transport)
```

แปลความหมาย:
- การผลิต 1 หน่วยของ Manufacturing ต้องใช้ Raw Material 0.5 หน่วย
- การผลิต 1 หน่วยของ Transport ต้องใช้ Manufacturing 0.3 หน่วย

#### Scaling Vector Computation

ให้ `f ∈ ℝⁿ` เป็น Final Demand Vector (ความต้องการสินค้าสุดท้าย)

**Scaling Vector:**
```
s = A⁻¹ · f
```

โดย `s ∈ ℝⁿ` คือระดับการดำเนินงานของแต่ละกระบวนการที่ต้องทำเพื่อตอบสนอง demand

**การพิสูจน์:**

เริ่มจาก Material Balance Equation:
```
A · s = f
```

คูณทั้งสองข้างด้วย A⁻¹:
```
A⁻¹ · A · s = A⁻¹ · f
I · s = A⁻¹ · f
s = A⁻¹ · f
```

#### Biosphere Matrix

**Biosphere Matrix B ∈ ℝᵐˣⁿ:**

```
B = [b₁₁  b₁₂  ...  b₁ₙ]
    [b₂₁  b₂₂  ...  b₂ₙ]
    [...  ...  ...  ...]
    [bₘ₁  bₘ₂  ...  bₘₙ]
```

โดย:
- `bᵢⱼ` = ปริมาณ emission i ที่ปล่อยออกต่อ 1 หน่วยของกระบวนการ j
- m = จำนวนชนิดของ emissions (CO₂, CH₄, N₂O, ...)

**Life Cycle Inventory (LCI):**
```
g = B · s = B · A⁻¹ · f
```

โดย `g ∈ ℝᵐ` คือปริมาณ emissions ทั้งหมดที่ปล่อยออกมา

#### Characterization Matrix

**Characterization Matrix Q ∈ ℝᵖˣᵐ:**

```
Q = [q₁₁  q₁₂  ...  q₁ₘ]
    [q₂₁  q₂₂  ...  q₂ₘ]
    [...  ...  ...  ...]
    [qₚ₁  qₚ₂  ...  qₚₘ]
```

โดย:
- `qᵢⱼ` = characterization factor สำหรับ emission j ใน impact category i
- p = จำนวน impact categories (GWP, AP, EP, ODP, ...)

**ตัวอย่าง GWP (Global Warming Potential):**
```
Q = [1.0  29.8  273.0  25200.0  ...]  (GWP-100 factors)
     CO₂  CH₄   N₂O    SF₆
```

**Life Cycle Impact Assessment (LCIA):**
```
h = Q · g = Q · B · s = Q · B · A⁻¹ · f
```

โดย `h ∈ ℝᵖ` คือผลกระทบสิ่งแวดล้อมในแต่ละ impact category

---

### ก.2 Leontief Inverse Matrix

#### Input-Output Model

ให้:
- `x ∈ ℝⁿ` = Total output vector (ผลผลิตรวมของแต่ละอุตสาหกรรม)
- `y ∈ ℝⁿ` = Final demand vector (ความต้องการสินค้าขั้นสุดท้าย)
- `Z ∈ ℝⁿˣⁿ` = Inter-industry transaction matrix

**Direct Requirements Matrix:**
```
A = Z · x̂⁻¹
```

โดย `x̂⁻¹` คือ diagonal matrix ของ 1/xᵢ

**Leontief Model:**
```
x = A · x + y
x - A · x = y
(I - A) · x = y
x = (I - A)⁻¹ · y
```

**Leontief Inverse:**
```
L = (I - A)⁻¹
```

เรียกว่า "Total Requirements Matrix" แสดงผลกระทบทั้งทางตรงและทางอ้อม

#### Environmental Extension

ให้ `F ∈ ℝᵐˣⁿ` เป็น Environmental Intensity Matrix (emissions per $ output)

**Total Environmental Impact:**
```
e = F · L · y = F · (I - A)⁻¹ · y
```

#### Infinite Series Expansion

Leontief Inverse สามารถเขียนเป็น Infinite Series:

```
L = (I - A)⁻¹ = I + A + A² + A³ + ... = Σ(k=0 to ∞) Aᵏ
```

**การพิสูจน์:**

สมมติ:
```
S = I + A + A² + A³ + ...
```

คูณทั้งสองข้างด้วย (I - A):
```
(I - A) · S = (I - A) · (I + A + A² + A³ + ...)
            = I - A + A - A² + A² - A³ + ...
            = I
```

ดังนั้น:
```
S = (I - A)⁻¹
```

**ความหมาย:**
- `I` = ผลกระทบทางตรง (Direct Impact)
- `A` = ผลกระทบทางอ้อมระดับ 1 (1st-order Indirect)
- `A²` = ผลกระทบทางอ้อมระดับ 2 (2nd-order Indirect)
- ...

---

### ก.3 Monte Carlo Uncertainty Propagation

#### ทฤษฎีความน่าจะเป็น

ให้ `X₁, X₂, ..., Xₙ` เป็น Random Variables (พารามิเตอร์ที่มีความไม่แน่นอน)

**ฟังก์ชันผลลัพธ์:**
```
Y = f(X₁, X₂, ..., Xₙ)
```

เป้าหมาย: หา Distribution ของ Y

#### วิธี Monte Carlo

**Algorithm:**
```
For k = 1 to N:
    1. Sample x₁⁽ᵏ⁾ ~ F₁(x₁)
    2. Sample x₂⁽ᵏ⁾ ~ F₂(x₂)
    ...
    3. Sample xₙ⁽ᵏ⁾ ~ Fₙ(xₙ)
    4. Compute y⁽ᵏ⁾ = f(x₁⁽ᵏ⁾, x₂⁽ᵏ⁾, ..., xₙ⁽ᵏ⁾)

Output:
    μ̂ᵧ = (1/N) Σ y⁽ᵏ⁾
    σ̂ᵧ² = (1/(N-1)) Σ (y⁽ᵏ⁾ - μ̂ᵧ)²
```

#### Central Limit Theorem

เมื่อ N → ∞:
```
μ̂ᵧ ~ N(μᵧ, σᵧ²/N)
```

**95% Confidence Interval:**
```
CI₀.₉₅ = [μ̂ᵧ - 1.96·σ̂ᵧ/√N, μ̂ᵧ + 1.96·σ̂ᵧ/√N]
```

#### Standard Error

```
SE = σ̂ᵧ / √N
```

**ตัวอย่าง:**
```
N = 10,000
σ̂ᵧ = 30 kg CO₂

SE = 30 / √10,000 = 30 / 100 = 0.3 kg CO₂
```

---

### ก.4 TOPSIS Algorithm

#### Step-by-Step Derivation

**Given:**
- Decision Matrix `X ∈ ℝᵐˣⁿ` (m alternatives, n criteria)
- Weight Vector `w ∈ ℝⁿ` where `Σ wⱼ = 1`
- Criteria Types: Benefit (↑) or Cost (↓)

**Step 1: Vector Normalization**

```
rᵢⱼ = xᵢⱼ / √(Σᵢ₌₁ᵐ xᵢⱼ²)
```

**เหตุผล:** ทำให้ทุก criteria อยู่ในมาตราส่วนเดียวกัน (0 ≤ rᵢⱼ ≤ 1)

**Step 2: Weighted Normalized Matrix**

```
vᵢⱼ = wⱼ · rᵢⱼ
```

**Step 3: Ideal Solutions**

```
v⁺ = {v₁⁺, v₂⁺, ..., vₙ⁺}  (Ideal Best)
v⁻ = {v₁⁻, v₂⁻, ..., vₙ⁻}  (Ideal Worst)
```

โดย:
```
vⱼ⁺ = max{vᵢⱼ | i=1,...,m}  if j is Benefit criterion
vⱼ⁺ = min{vᵢⱼ | i=1,...,m}  if j is Cost criterion

vⱼ⁻ = min{vᵢⱼ | i=1,...,m}  if j is Benefit criterion
vⱼ⁻ = max{vᵢⱼ | i=1,...,m}  if j is Cost criterion
```

**Step 4-5: Euclidean Distance**

```
dᵢ⁺ = √(Σⱼ₌₁ⁿ (vᵢⱼ - vⱼ⁺)²)  (Distance to Ideal Best)
dᵢ⁻ = √(Σⱼ₌₁ⁿ (vᵢⱼ - vⱼ⁻)²)  (Distance to Ideal Worst)
```

**Step 6: Relative Closeness**

```
Cᵢ = dᵢ⁻ / (dᵢ⁺ + dᵢ⁻)
```

**Properties:**
- `0 ≤ Cᵢ ≤ 1`
- `Cᵢ = 1` ⟺ Alternative i = Ideal Best (perfect)
- `Cᵢ = 0` ⟺ Alternative i = Ideal Worst (worst possible)
- `Cᵢ = 0.5` ⟺ Alternative i is equidistant from both ideals

**Step 7: Ranking**

จัดอันดับ alternatives ตามค่า Cᵢ จากมากไปน้อย

---

### ก.5 Sensitivity Analysis (Matrix Perturbation)

#### First-Order Perturbation

พิจารณาการเปลี่ยนแปลงเล็กน้อย (perturbation) ของ Matrix A:

```
A' = A + ε·ΔA
```

โดย ε << 1 (small perturbation parameter)

**Perturbed Inverse:**

ใช้ Neumann Series:
```
(A + ε·ΔA)⁻¹ ≈ A⁻¹ - ε·A⁻¹·ΔA·A⁻¹ + O(ε²)
```

**การพิสูจน์:**

ให้ `B = A + ε·ΔA`

```
B⁻¹ = (A + ε·ΔA)⁻¹
    = (A·(I + ε·A⁻¹·ΔA))⁻¹
    = (I + ε·A⁻¹·ΔA)⁻¹·A⁻¹
```

ใช้ Series Expansion:
```
(I + ε·M)⁻¹ ≈ I - ε·M + ε²·M² - ...
```

เมื่อ ε → 0:
```
B⁻¹ ≈ (I - ε·A⁻¹·ΔA)·A⁻¹
    ≈ A⁻¹ - ε·A⁻¹·ΔA·A⁻¹
```

#### Sensitivity of Impact

```
h = Q·B·A⁻¹·f

∂h/∂Aᵢⱼ = -Q·B·A⁻¹·Eᵢⱼ·A⁻¹·f
```

โดย `Eᵢⱼ` คือ Elementary Matrix (มีค่า 1 ที่ตำแหน่ง (i,j) และ 0 ที่อื่น)

#### Sensitivity Ratio

```
SRᵢⱼ = (∂h/∂pᵢⱼ) · (pᵢⱼ / h)
```

โดย pᵢⱼ คือพารามิเตอร์ใด ๆ ใน A หรือ B

**ความหมาย:**
- `|SRᵢⱼ| > 1` → ผลกระทบมีความอ่อนไหวสูงต่อพารามิเตอร์นี้
- `|SRᵢⱼ| < 1` → ผลกระทบมีความอ่อนไหวต่ำ
- `SRᵢⱼ > 0` → ความสัมพันธ์เชิงบวก (เพิ่ม p → เพิ่ม h)
- `SRᵢⱼ < 0` → ความสัมพันธ์เชิงลบ

---

## ภาคผนวก ข: โค้ดตัวอย่าง

### ข.1 Basic LCA Computation

```python
import numpy as np
from scipy.linalg import inv

# สร้าง simple supply chain
n_processes = 3

# Technology Matrix
A = np.array([
    [1.0, -0.5, 0.0],  # Raw Material
    [0.0,  1.0, -0.3], # Manufacturing
    [0.0,  0.0,  1.0]  # Transport
])

# Biosphere Matrix (Emission Factors)
B = np.diag([2.0, 5.0, 0.1])  # kg CO₂ per unit

# Characterization Matrix (GWP)
Q = np.ones((1, 3))  # All in CO₂-eq

# Final Demand
f = np.array([0, 1, 0])  # 1 unit of manufactured product

# Compute
s = inv(A) @ f           # Scaling vector
g = B @ s                 # Inventory
h = Q @ g                 # Impact

print("Scaling vector:", s)
print("Total emissions:", g)
print("Carbon footprint:", h[0], "kg CO₂-eq")
```

### ข.2 Monte Carlo Simulation

```python
import numpy as np

def monte_carlo_lca(A, B_mean, B_std, Q, f, n_sim=10000):
    """
    Monte Carlo LCA with uncertain Emission Factors
    """
    rng = np.random.default_rng(seed=42)
    results = []
    
    A_inv = inv(A)
    
    for k in range(n_sim):
        # Sample B matrix
        B_k = np.diag([
            max(0, rng.normal(B_mean[i], B_std[i]))
            for i in range(len(B_mean))
        ])
        
        # Compute impact
        s = A_inv @ f
        g = B_k @ s
        h = Q @ g
        results.append(h[0])
    
    results = np.array(results)
    
    return {
        'mean': np.mean(results),
        'std': np.std(results),
        'ci_95': (np.percentile(results, 2.5), np.percentile(results, 97.5)),
        'distribution': results
    }

# ใช้งาน
B_mean = [2.0, 5.0, 0.1]
B_std = [0.3, 0.6, 0.01]  # CV = 15%

result = monte_carlo_lca(A, B_mean, B_std, Q, f)
print(f"Carbon: {result['mean']:.2f} ± {result['std']:.2f} kg CO₂")
print(f"95% CI: [{result['ci_95'][0]:.2f}, {result['ci_95'][1]:.2f}]")
```

### ข.3 TOPSIS Implementation

```python
import numpy as np

def topsis(X, weights, criteria_types):
    """
    TOPSIS Multi-Criteria Decision Analysis
    
    X: decision matrix (m×n)
    weights: criteria weights (sum to 1)
    criteria_types: list of 'benefit' or 'cost'
    """
    # Step 1: Normalization
    col_norms = np.sqrt((X ** 2).sum(axis=0))
    R = X / col_norms
    
    # Step 2: Weighted matrix
    V = R * weights
    
    # Step 3: Ideal solutions
    ideal_best = []
    ideal_worst = []
    for j, ctype in enumerate(criteria_types):
        if ctype == 'benefit':
            ideal_best.append(V[:, j].max())
            ideal_worst.append(V[:, j].min())
        else:
            ideal_best.append(V[:, j].min())
            ideal_worst.append(V[:, j].max())
    
    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)
    
    # Step 4-5: Euclidean distances
    d_best = np.sqrt(((V - ideal_best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((V - ideal_worst) ** 2).sum(axis=1))
    
    # Step 6: Closeness coefficient
    C = d_worst / (d_best + d_worst)
    
    # Step 7: Ranking
    ranking = np.argsort(-C)
    
    return C, ranking

# ตัวอย่างการใช้งาน: เลือกซัพพลายเออร์
X = np.array([
    [100, 5000, 7, 8],   # Supplier A
    [150, 3000, 5, 9],   # Supplier B
    [80,  6000, 10, 7],  # Supplier C
])

weights = np.array([0.4, 0.3, 0.2, 0.1])
criteria_types = ['cost', 'cost', 'cost', 'benefit']

scores, ranking = topsis(X, weights, criteria_types)

print("TOPSIS Scores:", scores)
print("Ranking:", ['ABC'[i] for i in ranking])
```

---

## ภาคผนวก ค: คู่มือการใช้งาน

### ค.1 การติดตั้งและ Setup

#### ความต้องการของระบบ

**Hardware:**
- CPU: 2+ cores
- RAM: 4 GB ขึ้นไป
- Storage: 2 GB available
- Internet: Stable connection

**Software:**
- Python 3.10+
- Node.js 18+
- Git

#### ขั้นตอนการติดตั้ง

**1. Clone Repository**
```bash
git clone https://github.com/JayJayjj123456789/LCA-GPT.git
cd LCA-GPT
```

**2. Backend Setup**
```bash
# สร้าง virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# ติดตั้ง dependencies
pip install -r requirements.txt
```

**3. Frontend Setup**
```bash
cd frontend
npm install
cd ..
```

**4. Environment Variables**
```bash
# สร้างไฟล์ .env
cp .env.example .env

# แก้ไขด้วย text editor
nano .env
```

ใส่ค่า API keys:
```env
OPENROUTER_API_KEY=sk-or-...
NEO4J_URI=neo4j+ssc://...
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
SERPER_API_KEY=...
PINECONE_API_KEY=...
```

**5. รันระบบ**

Terminal 1 (Backend):
```bash
python -m uvicorn backend.main:app --reload --port 8001
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

เปิดเบราว์เซอร์: `http://localhost:5173`

---

### ค.2 การใช้งานพื้นฐาน

#### ขั้นตอนที่ 1: อัพโหลดเอกสาร

1. คลิก "Upload PDF" บนหน้า Dashboard
2. เลือกไฟล์ PDF (Invoice, PO, Report)
3. รองรับหลายไฟล์พร้อมกัน
4. รอการอัพโหลดเสร็จ (แถบสีเขียว)

#### ขั้นตอนที่ 2: วิเคราะห์ด้วย AI

1. คลิกปุ่ม "Run AI Carbon Audit"
2. รอประมาณ 30-60 วินาที (ขึ้นกับขนาดเอกสาร)
3. ระบบจะแสดง Progress Bar

#### ขั้นตอนที่ 3: ดูผลลัพธ์

**Dashboard Metrics:**
- Total Carbon Footprint (kg CO₂-eq)
- Supplier Name
- Items Tracked
- Optimization Score

**Supply Chain Graph:**
- แสดง Network Visualization
- Zoom in/out ด้วย Mouse Wheel
- Drag nodes เพื่อจัดตำแหน่ง
- Click node เพื่อดูรายละเอียด

**Analytics Charts:**
- Hotspot Bar Chart: Top 10 contributors
- Pie Chart: Breakdown by category
- Sankey Diagram: Flow analysis

**Data Tables:**
- Materials, Energy, Transport
- คลิก "View Source" เพื่อดูแหล่งอ้างอิง

#### ขั้นตอนที่ 4: Export Report

1. คลิก "Export PDF Report"
2. ระบบสร้าง ISO 14067 compliant report
3. ดาวน์โหลดอัตโนมัติ
4. เปิดด้วย PDF Reader

---

**สิ้นสุดภาคผนวก**
