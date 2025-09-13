#!/usr/bin/env python3
"""
Convert the Investment Management Module Specification to Word format
"""

import os
import sys
from pathlib import Path


def convert_to_word():
    """Convert markdown to Word document"""
    try:
        # Check if pandoc is available
        pandoc_check = os.system("which pandoc > /dev/null 2>&1")
        
        if pandoc_check == 0:
            print("🔧 Pandoc found! Converting to Word...")
            
            # Convert markdown to Word
            input_file = "INVESTMENT_MANAGEMENT_MODULE_SPECIFICATION.md"
            output_file = "INVESTMENT_MANAGEMENT_MODULE_SPECIFICATION.docx"
            
            # Enhanced pandoc command with better Word formatting
            command = f"""pandoc "{input_file}" -o "{output_file}" \
                --toc --toc-depth=3 \
                --number-sections \
                --highlight-style=tango \
                --reference-doc=reference.docx \
                --standalone"""
            
            # Try with basic command first
            basic_command = f'pandoc "{input_file}" -o "{output_file}" --toc --toc-depth=3 --number-sections'
            result = os.system(basic_command)
            
            if result == 0:
                print(f"✅ Successfully converted to {output_file}")
                print(f"📄 Document location: {Path(output_file).absolute()}")
                print(f"📊 File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
                return True
            else:
                print("❌ Pandoc conversion failed.")
                return False
        else:
            print("❌ Pandoc not available.")
            return False
            
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False


def install_pandoc():
    """Install pandoc if not available"""
    print("� Installing pandoc...")
    
    # Try to install pandoc
    install_result = os.system("apt-get update && apt-get install -y pandoc")
    
    if install_result == 0:
        print("✅ Pandoc installed successfully!")
        return True
    else:
        print("❌ Failed to install pandoc.")
        return False


def manual_conversion_instructions():
    """Provide manual conversion instructions"""
    print("\n" + "="*60)
    print("📋 MANUAL CONVERSION INSTRUCTIONS")
    print("="*60)
    print("\n1. Open the markdown file in VS Code:")
    print(f"   {Path('INVESTMENT_MANAGEMENT_MODULE_SPECIFICATION.md').absolute()}")
    print("\n2. Select all content (Ctrl+A)")
    print("\n3. Copy the content (Ctrl+C)")
    print("\n4. Open Microsoft Word")
    print("\n5. Paste the content (Ctrl+V)")
    print("\n6. Word will automatically format the document")
    print("\n7. Save as .docx format")
    print("\n8. Optional: Use Word's built-in styles for better formatting")
    print("   - Apply 'Heading 1' style to # headers")
    print("   - Apply 'Heading 2' style to ## headers")
    print("   - Apply 'Heading 3' style to ### headers")
    print("\n9. Optional: Insert automatic Table of Contents")
    print("   - Go to References > Table of Contents > Automatic")
    print("\n" + "="*60)


if __name__ == "__main__":
    print("🚀 Investment Management Module Specification - Word Conversion")
    print("="*65)
    
    # Check if input file exists
    input_file = Path("INVESTMENT_MANAGEMENT_MODULE_SPECIFICATION.md")
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)
    
    print(f"📄 Input file: {input_file}")
    print(f"📊 File size: {input_file.stat().st_size / 1024:.1f} KB")
    
    # Try conversion
    success = convert_to_word()
    
    if not success:
        print("\n🔧 Trying to install pandoc...")
        if install_pandoc():
            success = convert_to_word()
    
    if not success:
        manual_conversion_instructions()
    
    print("\n" + "="*65)
