

------

<p align="center">
  <img src="/polus_logo.png" alt="Polus Logo" width="400"/>
</p>


<h1 align="center">Polus</h1>

****



A DNA storage evaluation and reconstruction platform integrating multiple tools and algorithms.

------

## Option 1: Source Installation

### 1. Clone the Repository

```bash
git clone https://github.com/dinglulu/Polus.git
cd Polus
```

------

### 2. Environment Setup

#### 2.1 Main Python Environment

```bash
conda create -n Polus python=3.10
conda activate Polus

# Install PyTorch (CUDA 11.8 build)
pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu118  

# Install additional dependencies
pip install torchtune==0.5.0 torchao==0.8.0
pip install -r requirements.txt
```

#### 2.2 HEDGES Environment

```bash
conda create -n hedges python=2.7.18
conda activate hedges
pip install -r requirements_hedges.txt
```

------

### 3. Tool Installation

All external tools are located under `Polus/polls/Code/`.

#### 3.1 bsalign

- Repo: [ruanjue/bsalign](https://github.com/ruanjue/bsalign)
- Path: `Polus/polls/Code/reconstruct/bsalign`

```bash
cd polls/Code/reconstruct/bsalign
make
```

------

#### 3.2 BWA

- Repo: [lh3/bwa](https://github.com/lh3/bwa)
- Path: `Polus/polls/Code/bwa`

```bash
cd polls/Code/bwa
make
```

------

#### 3.3 Samtools

- Repo: [samtools/samtools](https://github.com/samtools/samtools)
- Path: `Polus/polls/Code/samtools/src`

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

#### 3.4 Badread

- Repo: [rrwick/Badread](https://github.com/rrwick/Badread)
- Path: `Polus/polls/Code/Badreadmain`

------

#### 3.5 dt4dds

- Repo: [fml-ethz/dt4dds](https://github.com/fml-ethz/dt4dds)
- Path: `Polus/polls/Code/dt4dds`

------

#### 3.6 BMALA

- Repo: [omersabary/Reconstruction](https://github.com/omersabary/Reconstruction)
- Path: `Polus/polls/Code/reconstruct/BMALA`

```bash
cd Polus/polls/Code/reconstruct/BMALA
g++ -std=c++11 BMALookahead.cpp -o DNA
```

------

#### 3.7 Iterative

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

#### 3.8 DivBMA

```bash
cd Polus/polls/Code/reconstruct/DivBMA
g++ -std=c++11 DividerBMA.cpp -o DivBMA
```

------

#### 3.9 Hybrid

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

### 4. Launch the Web Interface

Run from the project root:

```bash
python manage.py runserver 0.0.0.0:8045
```

Access via browser:

```
http://<server-ip>:8045/polls/decode
```

------

### 5. Project Structure Overview

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



## Option 2: Docker Deployment (Quick Start)

A prebuilt Docker image is provided via Google Drive:
 [Download polus_v1.tar.gz](https://drive.google.com/file/d/1EjWEA2DGRDQCrqG4XPTzbzqF0OKn0XQT/view?usp=sharing)

This method is recommended if you want to run POLUS quickly without manual environment setup.

------

### 1. Load the Docker Image

Download `polus_v1.tar.gz` and import it into Docker:

```
gunzip -c polus_v1.tar.gz | docker load
```

Verify the image is available:

```
docker images | grep polus
```

You should see `polus:v1`.

------

### 2. Run the Container (Mount Entire Project Directory)

Before running the Docker container, make sure you are inside the **Polus project directory**.
 For example:

```
cd Polus
```

Start the container and mount the entire project directory:

```
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

### 3. Verify and Access

Check running containers:

```
docker ps
```

View logs:

```
docker logs -f polus-app
```

Access POLUS in your browser:

- Local: http://localhost:8045/
- Remote: http://<server-ip>:8045/

Ensure port **8045** is open in your firewall or cloud security group.

------

<p align="center">
  <img src="/Polus - 9.28.png" alt="Polus Logo" width="400"/>
</p>