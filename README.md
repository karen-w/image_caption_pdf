```markdown
# PDF Image Caption Extractor

This Python script extracts images from PDF files and their corresponding captions, saving the images to subfolders and the results in a CSV file. It’s designed for academic papers or similar documents with embedded images and captions starting with "Figure" or "Fig."

## Features
- Extracts all images from PDF files in a specified folder.
- Identifies captions below images that start with "Figure" or "Fig."
- Infers captions for missing images based on the previous figure number.
- Saves images in subfolders named after the PDF and outputs a CSV with image paths and captions.

## Prerequisites
- **Python 3.9+**
- **Dependencies** (install via Conda):
  ```bash
  conda install -c conda-forge pymupdf pillow numpy
  ```
- **Operating System**: Tested on Linux (adaptable to Windows/macOS with path adjustments).

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/pdf-image-caption-extractor.git
   cd pdf-image-caption-extractor
   ```
2. Install dependencies in your Conda environment:
   ```bash
   conda activate your_env_name
   conda install -c conda-forge pymupdf
   ```

## Usage
1. **Prepare Your PDF**:
   - Place your PDF files in an input folder (e.g., `input/`).
   - Example PDF: [ocypodidae_systematics.pdf](ocypodidae_systematics.pdf) (from *Raffles Bulletin of Zoology 2016*).

2. **Run the Script**:
   - Use the provided Bash script or run directly:
     ```bash
     python3 pdf_image_caption_extractor.py <input_folder> <output_folder> <csv_output_path>
     ```
     Example:
     ```bash
     python3 pdf_image_caption_extractor.py input/ output/ output/image_captions.csv
     ```

3. **Output**:
   - Images are saved in `output/<pdf_name>/` (e.g., `output/ocypodidae_systematics/page_01_img_1.png`).
   - A CSV file (`image_captions.csv`) lists image paths and captions.

## How It Works

### 1. Image Extraction
The script uses **PyMuPDF** to extract images from each PDF page:
```python
image_list = page.get_images(full=True)
for img_index, img in enumerate(image_list):
    xref = img[0]
    base_image = pdf_file.extract_image(xref)
    image_bytes = base_image["image"]
    image_ext = base_image["ext"]
    image_name = f"page_{padded_page_num}_img_{padded_img_num}.{image_ext}"
    image_path = os.path.join(pdf_output_folder, image_name)
    with open(image_path, "wb") as image_file:
        image_file.write(image_bytes)
```

### 2. Caption Detection
Captions are identified by:
- Location: Below the image (`block_y0 > img_bottom_y`).
- Text: Starts with "Figure" or "Fig" (case-insensitive).
- Combines adjacent blocks within 1000 units for full captions:
```python
for i, block in enumerate(text_blocks):
    block_x0, block_y0, block_x1, block_y1, block_text, _, _ = block
    block_text_lower = block_text.strip().lower()
    if (block_y0 > img_bottom_y and 
        block_x0 <= img_info.x1 and 
        block_x1 >= img_info.x0 and
        (block_text_lower.startswith("figure") or block_text_lower.startswith("fig"))):
        full_caption = block_text.strip()
        if i + 1 < len(text_blocks):
            next_block = text_blocks[i + 1]
            next_y0 = next_block[1]
            if next_y0 <= block_y1 + 1000:
                full_caption += " " + next_block[4].strip()
        caption = full_caption
        break
```

### 3. Caption Inference
For images without a caption, it infers the next number based on the last caption:
```python
if caption == "Caption not found" and last_figure_num > 0:
    next_figure = last_figure_num + 1
    pattern = rf"(figure|fig)\s*{next_figure}\s*[:,.-]?\s*(.+?)(?:\n\n|\n\s*\n|$)"
    match = re.search(pattern, all_page_text, re.IGNORECASE)
    if match:
        caption = match.group(0).strip()
    else:
        caption = f"{last_figure_prefix} {next_figure}"
```

### Example Output
- **Input PDF**: `ocypodidae_systematics.pdf`
- **Extracted Image**: 
  ![Figure 5](sample_output/page_08_img_1.jpeg)
  *Caption*: "Fig. 5. Photographs of some species of the genus Ocypode."
- **CSV Snippet**:
  ```
  Image Path,Caption
  /home/user/output/ocypodidae_systematics/page_08_img_1.png,"Fig. 5. Photographs of some species of the genus Ocypode."
  /home/user/output/ocypodidae_systematics/page_10_img_1.png,"Figure 6"
  ```

## Tutorial: Extracting Images and Captions

### Step 1: Setup
- Download the example PDF: [ocypodidae_systematics.pdf](ocypodidae_systematics.pdf).
- Create an `input/` folder and place the PDF there.

### Step 2: Run the Script
```bash
python3 pdf_image_caption_extractor.py input/ output/ output/image_captions.csv
```

### Step 3: Verify Results
- Check `output/ocypodidae_systematics/` for images (e.g., `page_08_img_1.png` for Fig. 5).
- Open `output/image_captions.csv` in a spreadsheet or text editor.

![Sample Image](sample_output/page_08_img_1.jpeg)
*Caption extracted: "Fig. 5. Photographs of some species of the genus Ocypode."*

## Notes
- **Threshold**: The 1000-unit gap for caption blocks can be adjusted in the script.
- **Inference**: Assumes sequential figure numbers; tweak if your PDFs skip numbers.
- **Errors**: Ensure write permissions for the output folder.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributions
Feel free to fork, submit issues, or contribute improvements via pull requests!
```
