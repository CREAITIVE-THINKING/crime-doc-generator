# Crime Documentary Generator

An AI-powered application that generates true crime documentary segments from text documents. The application processes input documents, generates narrative segments, and creates a complete documentary with audio narration and visual elements.

## Features

- Document Processing
  - Supports PDF and TXT files
  - Handles encrypted PDFs
  - Multiple encoding support
  - Automatic text extraction

- Content Generation
  - AI-powered narrative segmentation
  - Dynamic image generation
  - Professional voiceover synthesis
  - Automated video compilation

- Experiment Tracking
  - Local experiment storage
  - Weights & Biases integration
  - Error logging and monitoring
  - Performance metrics tracking

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crime-doc-generator.git
cd crime-doc-generator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```env
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
WANDB_API_KEY=your_wandb_key
RUN_COMFY_API_KEY=your_runcomfy_key
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run main.py
```

2. Upload your source documents (PDF or TXT files)
3. Upload a character reference image
4. Select a voice for narration
5. Click "Generate Documentary Segments"

## Project Structure

```crime-doc-generator/README.md
crime-doc-generator/
├── main.py                 # Main Streamlit application
├── processors/
│   ├── document_processor.py   # Document processing and segmentation
│   ├── image_generator.py      # Image generation
│   ├── audio_generator.py      # Voice synthesis
│   ├── video_generator.py      # Video compilation
│   └── experiment_tracker.py   # Experiment tracking
├── experiments/           # Local storage for experiment data
├── requirements.txt       # Project dependencies
└── README.md             # Project documentation
```

## Dependencies

- OpenAI GPT-4 for text processing
- ElevenLabs for voice synthesis
- Weights & Biases for experiment tracking
- PyPDF2 for PDF processing
- Streamlit for the web interface

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4
- ElevenLabs for voice synthesis
- Weights & Biases for experiment tracking
- Streamlit for the amazing web framework
- RunComfy for VM image gen
```
