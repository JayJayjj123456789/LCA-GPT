# บทที่ 3: ขั้นตอนการดำเนินงาน

## 3.1 ภาพรวมขั้นตอน

โครงงานแบ่งการพัฒนาออกเป็น 5 ระยะหลัก:

```
Phase 1: Foundation & Setup (2 สัปดาห์)
    ↓
Phase 2: Mathematical Core (3 สัปดาห์)
    ↓
Phase 3: AI & Intelligence (2 สัปดาห์)
    ↓
Phase 4: Visualization & UX (2 สัปดาห์)
    ↓
Phase 5: Testing & Documentation (2 สัปดาห์)
```

---

## 3.2 Phase 1: Foundation & Setup

### วัตถุประสงค์
สร้างโครงสร้างพื้นฐานของระบบและทดสอบการเชื่อมต่อ

### ขั้นตอน

#### 3.2.1 ติดตั้ง Development Environment

```bash
# 1. Clone Repository
git clone https://github.com/JayJayjj123456789/LCA-GPT.git
cd LCA-GPT

# 2. สร้าง Python Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. ติดตั้ง Python Dependencies
pip install -r requirements.txt

# 4. ติดตั้ง Frontend Dependencies
cd frontend
npm install
cd ..

# 5. สร้างไฟล์ .env
cp .env.example .env
# แก้ไข .env ด้วย API keys จริง
```

#### 3.2.2 ตั้งค่า Neo4j Graph Database

```bash
# เลือก 1 ใน 3 วิธี:

# วิธีที่ 1: Neo4j Aura (Cloud - แนะนำ)
# 1. สมัครที่ https://console.neo4j.io
# 2. สร้าง Free Instance
# 3. คัดลอก URI, Username, Password มาใส่ใน .env

# วิธีที่ 2: Docker
docker run \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    neo4j:5-community

# วิธีที่ 3: Local Installation
# ดาวน์โหลดจาก https://neo4j.com/download/
```

#### 3.2.3 ตั้งค่า Pinecone Vector Database

```python
# ไฟล์: setup_pinecone.py
import pinecone

# Initialize Pinecone
pinecone.init(
    api_key="your_pinecone_api_key",
    environment="us-west1-gcp"
)

# สร้าง Index สำหรับเก็บ audit vectors
index_name = "lca-audits"
if index_name not in pinecone.list_indexes():
    pinecone.create_index(
        name=index_name,
        dimension=384,  # Sentence-BERT dimension
        metric="cosine"
    )
    print(f"Created index: {index_name}")
```

#### 3.2.4 ทดสอบการเชื่อมต่อ

```python
# ไฟล์: test_connections.py
import os
from neo4j import GraphDatabase
import pinecone
import openai

def test_neo4j():
    uri = os.getenv("NEO4J_URI")
    driver = GraphDatabase.driver(
        uri,
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    with driver.session() as session:
        result = session.run("RETURN 'Connection successful' AS message")
        print(result.single()["message"])
    driver.close()

def test_openrouter():
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )
    response = client.chat.completions.create(
        model="openrouter/owl-alpha",
        messages=[{"role": "user", "content": "Test"}],
        max_tokens=10
    )
    print("OpenRouter:", response.choices[0].message.content)

def test_pinecone():
    pinecone.init(
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-west1-gcp"
    )
    indexes = pinecone.list_indexes()
    print("Pinecone indexes:", indexes)

if __name__ == "__main__":
    test_neo4j()
    test_openrouter()
    test_pinecone()
```

### ผลลัพธ์ Phase 1
- ✅ Environment ติดตั้งครบถ้วน
- ✅ ทุก Service เชื่อมต่อได้
- ✅ Backend รันได้ที่ `localhost:8001`
- ✅ Frontend รันได้ที่ `localhost:5173`

---

## 3.3 Phase 2: Mathematical Core Development

### วัตถุประสงค์
สร้างโมดูลคำนวณทางคณิตศาสตร์หลัก

### 3.3.1 พัฒนา Technology Matrix (Heijungs Framework)

**ไฟล์:** `app/math/matrix_lca.py`

**ขั้นตอนการพัฒนา:**

1. **สร้าง Base Class**
```python
class TechnologyMatrix:
    def __init__(self, n_processes, n_emissions, n_impacts=1):
        self.A = np.eye(n_processes)  # Technology matrix
        self.B = np.zeros((n_emissions, n_processes))  # Biosphere matrix
        self.Q = np.zeros((n_impacts, n_emissions))  # Characterization matrix
```

2. **Implement Core Computations**
```python
def compute_scaling_vector(self, demand):
    """s = A⁻¹ · f"""
    return inv(self.A) @ demand

def compute_inventory(self, demand):
    """g = B · A⁻¹ · f"""
    s = self.compute_scaling_vector(demand)
    return self.B @ s

def compute_impact(self, demand):
    """h = Q · B · A⁻¹ · f"""
    s = self.compute_scaling_vector(demand)
    g = self.B @ s
    h = self.Q @ g
    return LCAResult(scaling_vector=s, inventory=g, impact_indicators=h, ...)
```

3. **เพิ่ม Builder Pattern**
```python
@classmethod
def from_supply_chain(cls, data):
    """Build matrices from LCA-GPT analysis JSON"""
    materials = data.get("materials", [])
    energies = data.get("energy", [])
    transports = data.get("transport", [])
    
    all_items = materials + energies + transports
    n = len(all_items)
    
    tm = cls(n_processes=n, n_emissions=n, n_impacts=1)
    
    # สร้าง B matrix จาก emission factors
    for i, item in enumerate(all_items):
        ef = item.get("emission_factor", 0)
        tm.B[i, i] = ef
    
    # Q matrix: แปลงเป็น CO₂-eq
    tm.Q = np.ones((1, n))
    
    return tm
```

### 3.3.2 พัฒนา Monte Carlo Uncertainty Module

**ไฟล์:** `app/math/uncertainty.py`

**ขั้นตอน:**

1. **สร้าง Parameter Distribution Class**
```python
@dataclass
class ParameterDistribution:
    dist_type: Literal["normal", "lognormal", "uniform", "triangular"]
    mean: float
    std: float = 0.0
    low: float = 0.0
    high: float = 0.0
    mode: float = 0.0
    
    def sample(self, rng, n=1):
        if self.dist_type == "normal":
            return rng.normal(self.mean, self.std, size=n)
        elif self.dist_type == "lognormal":
            # ... implementation
```

2. **Implement Monte Carlo Engine**
```python
class MonteCarloSimulation:
    def simulate(self, demand_vector, n_sim=10000):
        results = []
        for k in range(n_sim):
            # Sample B_k
            B_k = self.sample_biosphere_matrix()
            # Sample A_k
            A_k = self.sample_technology_matrix()
            # Compute h_k
            h_k = self.Q @ B_k @ inv(A_k) @ demand_vector
            results.append(h_k)
        
        # สถิติ
        mean = np.mean(results)
        std = np.std(results)
        ci_95 = (np.percentile(results, 2.5), np.percentile(results, 97.5))
        
        return UncertaintyResult(mean=mean, std=std, ci_95=ci_95, ...)
```

### 3.3.3 พัฒนา TOPSIS Multi-Criteria Module

**ไฟล์:** `app/math/topsis.py`

**Algorithm Implementation:**

```python
class TOPSIS:
    def rank(self, alternatives, criteria, decision_matrix, weights, criteria_types):
        X = np.asarray(decision_matrix)
        w = np.asarray(weights)
        
        # Step 1: Normalization
        col_norms = np.sqrt((X ** 2).sum(axis=0))
        R = X / col_norms
        
        # Step 2: Weighted matrix
        V = R * w
        
        # Step 3: Ideal solutions
        ideal_best = []
        ideal_worst = []
        for j, ctype in enumerate(criteria_types):
            if ctype == "benefit":
                ideal_best.append(V[:, j].max())
                ideal_worst.append(V[:, j].min())
            else:  # cost
                ideal_best.append(V[:, j].min())
                ideal_worst.append(V[:, j].max())
        
        # Step 4-5: Euclidean distances
        d_best = np.sqrt(((V - ideal_best) ** 2).sum(axis=1))
        d_worst = np.sqrt(((V - ideal_worst) ** 2).sum(axis=1))
        
        # Step 6: Closeness coefficient
        C = d_worst / (d_best + d_worst)
        
        # Step 7: Ranking
        sorted_indices = np.argsort(-C)
        rankings = [
            {
                "rank": i+1,
                "alternative": alternatives[idx],
                "closeness_coefficient": C[idx],
                ...
            }
            for i, idx in enumerate(sorted_indices)
        ]
        
        return TOPSISResult(rankings=rankings, ...)
```

### 3.3.4 Unit Testing

**ไฟล์:** `tests/test_math.py`

```python
import pytest
import numpy as np
from app.math.matrix_lca import TechnologyMatrix
from app.math.uncertainty import MonteCarloSimulation
from app.math.topsis import TOPSIS

def test_technology_matrix_basic():
    tm = TechnologyMatrix(n_processes=3, n_emissions=3, n_impacts=1)
    
    # ตั้งค่า matrices
    tm.A = np.eye(3)
    tm.B = np.diag([2.5, 5.0, 0.1])
    tm.Q = np.ones((1, 3))
    
    # Demand
    demand = np.array([0, 1, 0])
    
    # คำนวณ
    result = tm.compute_impact(demand)
    
    # ตรวจสอบ
    assert result.total_impact > 0
    assert len(result.scaling_vector) == 3

def test_monte_carlo_convergence():
    # สร้าง simple model
    tm = TechnologyMatrix(n_processes=2, n_emissions=2, n_impacts=1)
    tm.A = np.eye(2)
    tm.B = np.diag([2.0, 3.0])
    tm.Q = np.ones((1, 2))
    
    # Monte Carlo
    mc = MonteCarloSimulation(tm)
    mc.set_emission_factor_uncertainty(0, dist_type="normal", mean=2.0, std=0.2)
    mc.set_emission_factor_uncertainty(1, dist_type="normal", mean=3.0, std=0.3)
    
    demand = np.array([1, 1])
    result = mc.simulate(demand, n_sim=1000)
    
    # ตรวจสอบ CI
    assert result.ci_95[0] < result.mean < result.ci_95[1]
    assert result.std > 0

def test_topsis_ranking():
    topsis = TOPSIS()
    
    # Supplier comparison
    result = topsis.rank(
        alternatives=["A", "B", "C"],
        criteria=["Carbon", "Cost", "Quality"],
        decision_matrix=np.array([
            [100, 5000, 8],
            [150, 3000, 9],
            [80, 6000, 7],
        ]),
        weights=[0.5, 0.3, 0.2],
        criteria_types=["cost", "cost", "benefit"]
    )
    
    # ตรวจสอบ
    assert len(result.rankings) == 3
    assert result.rankings[0]["rank"] == 1
    assert 0 <= result.rankings[0]["closeness_coefficient"] <= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### ผลลัพธ์ Phase 2
- ✅ TechnologyMatrix ทำงานได้ถูกต้องตาม Heijungs Framework
- ✅ Monte Carlo Simulation ให้ผล Mean ± CI
- ✅ TOPSIS จัดอันดับได้ตามเกณฑ์
- ✅ Unit Tests ผ่านทั้งหมด (19 tests)

---

## 3.4 Phase 3: AI & Intelligence Features

### วัตถุประสงค์
พัฒนาความสามารถ AI สำหรับวิเคราะห์เอกสารและค้นหาข้อมูล

### 3.4.1 PDF Extraction & AI Analysis

**ไฟล์:** `app/analyzer.py`

```python
def extract_text_from_pdf(file_path: str) -> str:
    """ใช้ PyMuPDF แยกข้อความจาก PDF"""
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def analyze_enterprise_carbon(text: str) -> dict:
    """ใช้ Owl-Alpha LLM วิเคราะห์และแยกข้อมูล"""
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )
    
    system_prompt = """
    You are an Expert LCA Sustainability Consultant.
    Extract carbon footprint data from supply chain documents.
    
    Return JSON with structure:
    {
      "project_info": {...},
      "materials": [{name, amount, unit, emission_factor, note}],
      "energy": [{type, usage, unit, emission_factor, note}],
      "transport": [{method, distance, unit, emission_factor, note}],
      "total_estimated_co2": float,
      "recommendations": [...]
    }
    """
    
    response = client.chat.completions.create(
        model="openrouter/owl-alpha",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze: {text}"}
        ],
        temperature=0.1
    )
    
    return json.loads(response.choices[0].message.content)
```

### 3.4.2 Emission Factor Search

**ไฟล์:** `app/search.py`

```python
def search_emission_factor(material: str, serper_api_key: str) -> dict:
    """ค้นหา Emission Factor จาก Google Search"""
    query = f"{material} carbon footprint emission factor kg CO2"
    
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": serper_api_key},
        json={"q": query, "num": 5}
    )
    
    results = response.json().get("organic", [])
    
    # แยก URL ที่น่าเชื่อถือ
    trusted_domains = [
        "ghgprotocol.org",
        "ipcc.ch",
        "ecoinvent.org",
        "epa.gov"
    ]
    
    for result in results:
        url = result.get("link", "")
        if any(domain in url for domain in trusted_domains):
            return {
                "title": result.get("title"),
                "url": url,
                "snippet": result.get("snippet")
            }
    
    return {"url": "https://ghgprotocol.org/", "title": "GHG Protocol (Fallback)"}
```

### 3.4.3 Vector Store for Past Audits

**ไฟล์:** `app/vector_store.py`

```python
from sentence_transformers import SentenceTransformer
import pinecone

model = SentenceTransformer('all-MiniLM-L6-v2')

def store_audit(project_name: str, summary: str, total_co2: float, materials: list):
    """เก็บ audit ลง Pinecone Vector DB"""
    # สร้าง embedding
    text = f"{project_name}. {summary}. Materials: {', '.join(materials)}"
    embedding = model.encode(text).tolist()
    
    # Store
    index = pinecone.Index("lca-audits")
    index.upsert([
        (
            f"audit_{int(time.time())}",
            embedding,
            {
                "project": project_name,
                "summary": summary,
                "total_co2": total_co2,
                "materials": materials
            }
        )
    ])

def find_similar_audits(materials: list, top_k: int = 5) -> list:
    """ค้นหา audit ที่คล้ายกันจาก materials"""
    query_text = f"Materials: {', '.join(materials)}"
    query_embedding = model.encode(query_text).tolist()
    
    index = pinecone.Index("lca-audits")
    results = index.query(query_embedding, top_k=top_k, include_metadata=True)
    
    return [
        {
            "project": match.metadata["project"],
            "total_co2": match.metadata["total_co2"],
            "similarity": match.score
        }
        for match in results.matches
    ]
```

### ผลลัพธ์ Phase 3
- ✅ อ่าน PDF และแยกข้อมูลได้อัตโนมัติ
- ✅ AI วิเคราะห์และคืน JSON structure ที่ถูกต้อง
- ✅ ค้นหา Emission Factor จาก Google Search ได้
- ✅ เก็บและค้นหา Past Audits ด้วย Semantic Search

---

**หมายเหตุ:** เนื่องจากเนื้อหายาว จะแยกเป็นหลายไฟล์เพื่อความชัดเจน
