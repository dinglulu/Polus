# 🧬 **POLUS**
<p align="center">
  <img src="/Polus - 9.28.png" alt="Polus Logo" width="1600"/>
</p>
------

> ⚙️ **POLUS** is a comprehensive evaluation and reconstruction platform for **DNA data storage**, integrating multiple codec algorithms, simulators, and reconstruction methods with an interactive web interface and containerized deployment.

------

## 📦 **Option 1: Source Installation**

### 🧩 Step 1 — Clone the Repository

```bash
git clone https://github.com/dinglulu/Polus.git
cd Polus
```

------

### ⚙️ Step 2 — Environment Setup

#### 🧠 2.1 Main Python Environment

```bash
conda create -n Polus python=3.10
conda activate Polus

# Install PyTorch (CUDA 11.8 build)
pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu118  

# Additional dependencies
pip install torchtune==0.5.0 torchao==0.8.0
pip install -r requirements.txt
```

#### 🧬 2.2 HEDGES Environment

```bash
conda create -n hedges python=2.7.18
conda activate hedges
pip install -r requirements_hedges.txt
```

------

### 🔧 Step 3 — Tool Installation

All reconstruction and decoding tools are located under:

```
Polus/polls/Code/
```

#### 🔹 3.1 BSAlign

- **Repo:** [ruanjue/bsalign](https://github.com/ruanjue/bsalign)
- **Path:** `Polus/polls/Code/reconstruct/bsalign`

```bash
cd polls/Code/reconstruct/bsalign
make
```

------

#### 🔹 3.2 BWA

- **Repo:** [lh3/bwa](https://github.com/lh3/bwa)
- **Path:** `Polus/polls/Code/bwa`

```bash
cd polls/Code/bwa
make
```

------

#### 🔹 3.3 Samtools

- **Repo:** [samtools/samtools](https://github.com/samtools/samtools)
- **Path:** `Polus/polls/Code/samtools/src`

```bash
cd polls/Code/samtools/src

# Extract source files
tar -xjf htslib-1.18.tar.bz2
tar -xjf samtools-1.18.tar.bz2

# Build htslib
cd htslib-1.18
./configure --prefix=$(pwd)/install
make && make install
cd ..

# Build samtools
cd samtools-1.18
./configure --prefix=$(pwd)/install --with-htslib=$(pwd)/../htslib-1.18/install
make && make install
cd ..
```

Add the following to your `~/.bashrc`:

```bash
# Replace "your_path" with the absolute path where you cloned Polus
export PATH=your_path/Polus/polls/Code/samtools/src/htslib-1.18/install/bin:$PATH
export PATH=your_path/Polus/polls/Code/samtools/src/samtools-1.18/install/bin:$PATH
export LD_LIBRARY_PATH=your_path/Polus/polls/Code/samtools/src/htslib-1.18/install/lib:$LD_LIBRARY_PATH
```

------

#### 🔹 3.4 BMALA

- **Repo:** [omersabary/Reconstruction](https://github.com/omersabary/Reconstruction)
- **Path:** `Polus/polls/Code/reconstruct/BMALA`

```bash
cd Polus/polls/Code/reconstruct/BMALA
g++ -std=c++11 BMALookahead.cpp -o DNA
```

------

#### 🔹 3.5 Iterative Reconstruction

```bash
cd Polus/polls/Code/reconstruct/Iterative

g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o LCS2.o LCS2.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o EditDistance.o EditDistance.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o Clone.o Clone.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o Cluster2.o Cluster2.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o LongestPath.o LongestPath.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o CommonSubstring2.o CommonSubstring2.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o DividerBMA.o DividerBMA.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o DNA.o DNA.cpp
g++ -o DNA *.o
```

------

#### 🔹 3.6 DivBMA

```bash
cd Polus/polls/Code/reconstruct/DivBMA
g++ -std=c++11 DividerBMA.cpp -o DivBMA
```

------

#### 🔹 3.7 Hybrid Reconstruction

```bash
cd Polus/polls/Code/reconstruct/Hybrid

g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o LCS2.o LCS2.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o EditDistance.o EditDistance.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o Clone.o Clone.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o Cluster2.o Cluster2.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o LongestPath.o LongestPath.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o CommonSubstring2.o CommonSubstring2.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o DividerBMA.o DividerBMA.cpp
g++ -std=c++0x -O3 -g3 -Wall -c -fmessage-length=0 -o DNA.o DNA.cpp
g++ -o DNA *.o
```

------

#### 🔹 3.8 Badread & dt4dds

| Tool          | Repository                                            | Path                            |
| ------------- | ----------------------------------------------------- | ------------------------------- |
| 🧫 **Badread** | [rrwick/Badread](https://github.com/rrwick/Badread)   | `Polus/polls/Code/Badreadmain/` |
| 🔬 **dt4dds**  | [fml-ethz/dt4dds](https://github.com/fml-ethz/dt4dds) | `Polus/polls/Code/dt4dds/`      |

------

### 🌐 Step 4 — Launch Web Interface

Run from project root:

```bash
python manage.py runserver 0.0.0.0:8045
```

Access via browser:

```
http://<server-ip>:8045/polls/decode
```

------

### 🗂️ Step 5 — Project Structure

```
Polus/
├── polls/
│   ├── Code/
│   │   ├── reconstruct/
│   │   │   ├── bsalign/
│   │   │   ├── BMALA/
│   │   │   ├── Iterative/
│   │   │   ├── DivBMA/
│   │   │   └── Hybrid/
│   │   ├── bwa/
│   │   ├── samtools/
│   │   ├── Badreadmain/
│   │   └── dt4dds/
│   └── ...
├── requirements.txt
├── requirements_hedges.txt
└── manage.py
```

------

# 🐳 **Option 2: Docker Deployment (Quick Start)**

> 🧩 Recommended for users who want to run POLUS quickly without setting up dependencies.

### 🔹 Step 1 — Download Prebuilt Image

📥 [Download polus_v1.tar.gz](https://drive.google.com/file/d/1EjWEA2DGRDQCrqG4XPTzbzqF0OKn0XQT/view?usp=sharing)

------

### 🔹 Step 2 — Load Docker Image

```bash
gunzip -c polus_v1.tar.gz | docker load
docker images | grep polus
```

You should see:

```
polus:v1
```

------

### 🔹 Step 3 — Run Container

```bash
docker run -d \
  --name polus-app \
  -p 8045:8045 \
  -v $(pwd):/app \
  -e TZ=Asia/Shanghai \
  -w /app \
  --restart unless-stopped \
  polus:v1 \
  bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate POLUS && python manage.py runserver 0.0.0.0:8045"
```

------

### 🔹 Step 4 — Verify and Access

Check container:

```bash
docker ps
```

View logs:

```bash
docker logs -f polus-app
```

Access POLUS:

- 🌐 Local: http://localhost:8045/
- 🌐 Remote: `http://<server-ip>:8045/`

> 🧱 Ensure port **8045** is open in your firewall or cloud security group.

------

## 📘 Citation

If you use **POLUS** in your research, please cite:

> *POLUS: A Modular Platform for DNA Storage Evaluation and Reconstruction.*

------




