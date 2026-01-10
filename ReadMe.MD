# QID - Query Images by Description

🔍 A semantic image search system that lets you find images using natural language descriptions.

## ✨ Features

- **Natural Language Search**: Find images using everyday language like "sunset at the beach" or "a cute dog"
- **Semantic Understanding**: Powered by OpenAI's CLIP model - understands meaning, not just keywords
- **Fast & Efficient**: Uses FAISS for lightning-fast similarity search
- **GPU Accelerated**: Leverages your GPU for 6-10x faster processing
- **Completely Offline**: Your images and searches stay private on your machine
- **Batch Processing**: Index entire folders with progress tracking
- **Smart Filtering**: Automatically skips already-processed images

## 🏗️ Architecture

```
Text Query → Text Encoder (CLIP) → Vector (512-dim)
                                         ↓
                                   Vector Store (FAISS)
                                         ↓
                                   Similar Vector IDs
                                         ↓
                                   Metadata Store (SQLite)
                                         ↓
                                   Image Results
```

## 🚀 Getting Started

### 1. Installation

```bash
# Clone or create project
cd QID

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Setup

```bash
python test_setup.py
```

Should show:
- ✅ All libraries imported
- ✅ GPU detected (if available)
- ✅ CLIP model loaded

### 3. Add Images
Add your own images
```bash
# Copy images to data/images/
cp /path/to/your/photos/* data/images/
```

### 4. Index Images

```bash
python test_pipeline.py
```

This will:
1. Scan `data/images/` for images
2. Validate all images
3. Encode images to vectors (GPU accelerated!)
4. Store in database

### 5. Search!

The pipeline script includes an interactive search:
```
🔍 Enter search query: sunset at the beach

✅ Found 5 results:
1. sunset.jpg (95% match)
2. ocean_view.jpg (89% match)
3. beach_day.jpg (87% match)
```

## 📁 Project Structure

```
QID/
├── config/
│   └── config.yaml              # Configuration
├── src/
│   ├── embeddings/
│   │   ├── image_encoder.py     # Image → Vector
│   │   └── text_encoder.py      # Text → Vector
│   ├── database/
│   │   ├── vector_store.py      # FAISS vector database
│   │   └── metadata_store.py    # SQLite metadata
│   ├── ingestion/
│   │   ├── image_processor.py   # Image validation
│   │   └── batch_indexer.py     # Batch processing
│   ├── query/
│   │   └── search_engine.py     # Search functionality
│   └── utils/
│       ├── config.py             # Config management
│       └── logger.py             # Logging
├── ui/                           # Tkinter UI (coming soon!)
├── data/
│   ├── images/                   # Your images
│   ├── embeddings/               # Vector database
│   └── metadata/                 # Image metadata
└── models/                       # Downloaded CLIP models
```



## 📊 Performance

**Hardware: RTX 3050 GPU**

| Task | CPU | GPU | Speedup |
|------|-----|-----|---------|
| Encode 100 images | 30s | 5s | 6x |
| Encode 1000 images | 5min | 50s | 6x |
| Search 10K images | 50ms | 50ms | 1x* |
| Text encoding | 100ms | 10ms | 10x |

*FAISS-CPU is already very fast for personal libraries

**Memory Usage:**
- 10,000 images: ~25MB (vectors) + 2MB (metadata)
- CLIP model: 350MB
- Peak GPU memory: ~500MB

## 🐛 Troubleshooting

### CUDA not detected
- Check: `nvidia-smi`
- Reinstall PyTorch with CUDA: See installation steps

### Images not found
- Check `data/images/` exists
- Verify supported formats: `.jpg`, `.png`, `.bmp`, `.gif`, `.webp`

### Out of memory
- Reduce `batch_size` in config
- Use smaller model: `ViT-B/32` instead of `ViT-L/14`

### Import errors
- Ensure virtual environment is activated
- Check VS Code is using correct Python interpreter

## 🚦 Current Status

✅ **Completed:**
- Image & text encoding (CLIP)
- Vector database (FAISS)
- Metadata storage (SQLite)
- Batch indexing pipeline
- Natural language search
- CLI interface

🚧 **In Progress:**
- Advanced UI (next phase!)


## 📚 Learn More

- [CLIP Paper](https://arxiv.org/abs/2103.00020)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Vector Embeddings Explained](https://www.pinecone.io/learn/vector-embeddings/)


## 🤝 Contributing

This is a learning project! Feel free to:
- Add features
- Fix bugs
- Improve documentation
- Share your improvements

---

**Made with ❤️ for learning AI and building practical tools**