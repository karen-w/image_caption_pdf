# -*- coding: utf-8 -*-
import fitz  # PyMUDF
import os
import glob
import sys
import csv
import re

sys.dont_write_bytecode = True

def extract_images_and_captions(input_folder, output_folder, csv_output_path):
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"CSV output: {csv_output_path}")

    os.makedirs(output_folder, exist_ok=True)
    image_caption_table = []
    pdf_files = glob.glob(os.path.join(input_folder, "*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {input_folder}")
        return
    print(f"Found {len(pdf_files)} PDF files to process.")

    for pdf_path in pdf_files:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        pdf_output_folder = os.path.join(output_folder, pdf_name)
        os.makedirs(pdf_output_folder, exist_ok=True)

        try:
            pdf_file = fitz.open(pdf_path)
            print(f"Processing: {pdf_name}")
            total_pages = len(pdf_file)
            page_digits = len(str(total_pages))
            last_figure_num = 0  # Track the last figure number for inference
            last_figure_prefix = "Figure"  # Default prefix, updated based on last caption

            for page_num in range(total_pages):
                page = pdf_file[page_num]
                image_list = page.get_images(full=True)
                total_images = len(image_list)
                img_digits = len(str(total_images)) if total_images > 0 else 1
                text_blocks = page.get_text("blocks")
                all_page_text = page.get_text("text")  # Full page text for searching

                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf_file.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    padded_page_num = str(page_num + 1).zfill(page_digits)
                    padded_img_num = str(img_index + 1).zfill(img_digits)
                    image_name = f"page_{padded_page_num}_img_{padded_img_num}.{image_ext}"
                    image_path = os.path.join(pdf_output_folder, image_name)

                    with open(image_path, "wb") as image_file:
                        image_file.write(image_bytes)
                    print(f"  Saved: {image_path}")

                    img_info = page.get_image_bbox(img)
                    img_bottom_y = img_info.y1

                    caption = "Caption not found"
                    # Look for caption directly below the image
                    for i, block in enumerate(text_blocks):
                        block_x0, block_y0, block_x1, block_y1, block_text, _, _ = block
                        block_text_lower = block_text.strip().lower()
                        if (block_y0 > img_bottom_y and 
                            block_x0 <= img_info.x1 and 
                            block_x1 >= img_info.x0 and
                            (block_text_lower.startswith("figure") or block_text_lower.startswith("fig"))):
                            # Combine with the next block if it’s part of the caption
                            full_caption = block_text.strip()
                            if i + 1 < len(text_blocks):
                                next_block = text_blocks[i + 1]
                                next_y0 = next_block[1]
                                if next_y0 <= block_y1 + 1000:  # Threshold of 1000
                                    full_caption += " " + next_block[4].strip()
                            caption = full_caption
                            # Extract figure number and prefix for inference
                            match = re.search(r"(figure|fig)\s*(\d+)", block_text_lower, re.IGNORECASE)
                            if match:
                                last_figure_prefix = match.group(1).capitalize()  # "Figure" or "Fig"
                                last_figure_num = int(match.group(2))
                            break

                    # If no caption found, infer from previous figure number with prefix and space
                    if caption == "Caption not found" and last_figure_num > 0:
                        next_figure = last_figure_num + 1
                        # Search for "Figure X" or "Fig X" in the full page text
                        pattern = rf"(figure|fig)\s*{next_figure}\s*[:,.-]?\s*(.+?)(?:\n\n|\n\s*\n|$)"
                        match = re.search(pattern, all_page_text, re.IGNORECASE)
                        if match:
                            caption = match.group(0).strip()
                            last_figure_num = next_figure
                            last_figure_prefix = match.group(1).capitalize()  # Update prefix
                        else:
                            # Use last prefix with space and number
                            caption = f"{last_figure_prefix}. {next_figure}"
                            last_figure_num = next_figure

                    image_caption_table.append([image_path, caption])

            pdf_file.close()
            print(f"Finished processing: {pdf_name}")

        except Exception as e:
            print(f"Error processing {pdf_name}: {str(e)}")

    if image_caption_table:
        with open(csv_output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Image Path", "Caption"])
            writer.writerows(image_caption_table)
        print(f"Caption table saved to: {csv_output_path}")
    else:
        print("No images or captions extracted.")

    print("All PDFs processed!")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 pdf_image_caption_extractor.py <input_folder> <output_folder> <csv_output_path>")
        print("Error: Incorrect number of arguments provided.")
        print(f"Expected 3 arguments, got {len(sys.argv) - 1}")
        print(f"Arguments received: {sys.argv[1:]}")
        sys.exit(1)
    else:
        my_input_folder = sys.argv[1]
        my_output_folder = sys.argv[2]
        my_csv_output = sys.argv[3]
        extract_images_and_captions(my_input_folder, my_output_folder, my_csv_output)