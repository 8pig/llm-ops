import os
from pathlib import Path
from typing import List, Optional


def read_pdf_with_langchain_pypdf(pdf_path: str) -> List:
    """
    使用 LangChain PyPDFLoader 读取 PDF

    Args:
        pdf_path: PDF 文件路径

    Returns:
        Document 对象列表，每个对象包含一页内容
    """
    try:
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(pdf_path)
        pages = loader.load()

        print(f"📄 PDF 页数：{len(pages)}")

        return pages

    except ImportError:
        print("错误：请先安装依赖\n运行：uv add pypdf2 langchain-community")
        return []
    except Exception as e:
        print(f"读取失败：{str(e)}")
        return []


def read_pdf_with_langchain_pdfplumber(pdf_path: str) -> List:
    """
    使用 LangChain PDFPlumberLoader 读取 PDF（推荐，中文支持更好）

    Args:
        pdf_path: PDF 文件路径

    Returns:
        Document 对象列表
    """
    try:
        from langchain_community.document_loaders import PDFPlumberLoader

        loader = PDFPlumberLoader(pdf_path)
        pages = loader.load()

        print(f"📄 PDF 页数：{len(pages)}")

        return pages

    except ImportError:
        print("错误：请先安装依赖\n运行：uv add pdfplumber langchain-community")
        return []
    except Exception as e:
        print(f"读取失败：{str(e)}")
        return []


def read_pdf_with_langchain_pymupdf(pdf_path: str) -> List:
    """
    使用 LangChain PyMuPDFLoader 读取 PDF（性能最好）

    Args:
        pdf_path: PDF 文件路径

    Returns:
        Document 对象列表
    """
    try:
        from langchain_community.document_loaders import PyMuPDFLoader

        loader = PyMuPDFLoader(pdf_path)
        pages = loader.load()

        print(f"📄 PDF 页数：{len(pages)}")

        return pages

    except ImportError:
        print("错误：请先安装依赖\n运行：uv add pymupdf langchain-community")
        return []
    except Exception as e:
        print(f"读取失败：{str(e)}")
        return []


def read_pdf_with_ocr(pdf_path: str, lang: str = 'chi_sim') -> List:
    """
    使用 LangChain 的 OCR 方式读取扫描版 PDF

    Args:
        pdf_path: PDF 文件路径
        lang: OCR 语言

    Returns:
        Document 对象列表
    """
    try:
        from langchain_community.document_loaders import ImageCaptionLoader
        from langchain_community.document_loaders import UnstructuredPDFLoader

        # 使用 UnstructuredPDFLoader（支持 OCR）
        loader = UnstructuredPDFLoader(pdf_path, mode="single", strategy="ocr_only")
        pages = loader.load()

        print(f"📄 PDF 页数：{len(pages)} (OCR 模式)")

        return pages

    except ImportError:
        print("错误：请先安装依赖\n运行：uv add unstructured pdf2image pillow pytesseract langchain-community")
        print("还需要安装 Tesseract-OCR: https://github.com/tesseract-ocr/tesseract")
        return []
    except Exception as e:
        print(f"OCR 识别失败：{str(e)}")
        return []


def split_documents(documents: List, chunk_size: int = 2000, chunk_overlap: int = 200):
    """
    使用 LangChain 的文本分割器分割文档

    Args:
        documents: Document 对象列表
        chunk_size: 每块大小
        chunk_overlap: 重叠部分大小

    Returns:
        分割后的文档块列表
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", ""]
        )

        splits = text_splitter.split_documents(documents)

        print(f"📝 分割完成：共 {len(splits)} 个文本块")

        return splits

    except ImportError:
        print("错误：请先安装依赖\n运行：uv add langchain-text-splitters")
        return []
    except Exception as e:
        print(f"分割失败：{str(e)}")
        return []


# 主程序
if __name__ == "__main__":
    # PDF 文件路径
    pdf_file = "./9900000000080295/补充协议-企业.pdf"

    # 检查文件是否存在
    if not os.path.exists(pdf_file):
        print(f"❌ 文件不存在：{pdf_file}")
        print("\n请确保 PDF 文件在当前目录下")
        exit(1)

    print("=" * 60)
    print(f"📄 开始读取 PDF: {pdf_file}")
    print("=" * 60)

    # 方法 1: 使用 PDFPlumberLoader（推荐）
    print("\n✨ 使用 LangChain PDFPlumberLoader 读取...\n")
    pages = read_pdf_with_langchain_pdfplumber(pdf_file)

    if not pages:
        # 尝试 PyMuPDFLoader
        print("\n尝试使用 LangChain PyMuPDFLoader 读取...\n")
        pages = read_pdf_with_langchain_pymupdf(pdf_file)

    if pages:
        # 显示第一页的内容和元数据
        print("\n" + "=" * 60)
        print("📋 第一页信息:")
        print("=" * 60)
        first_page = pages[0]
        print(f"页面内容长度：{len(first_page.page_content)}")
        print(f"元数据：{first_page.metadata}")

        print("\n" + "=" * 60)
        print("📝 PDF 内容预览（前 500 字符）:")
        print("=" * 60)
        all_content = "\n".join([page.page_content for page in pages])
        print(all_content[:500])
        print("\n..." if len(all_content) > 500 else "")

        # 保存到文本文件
        output_file = pdf_file.replace(".pdf", "_langchain.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(all_content)
        print(f"\n✅ 内容已保存到：{output_file}")

        # 可选：分割文档
        print("\n" + "=" * 60)
        print("✂️  分割文档为小块...")
        print("=" * 60)
        chunks = split_documents(pages, chunk_size=500, chunk_overlap=50)

        if chunks:
            print(f"\n前 3 个文本块预览:")
            for i, chunk in enumerate(chunks[:3], 1):
                print(f"\n--- 块 {i} ---")
                print(f"长度：{len(chunk.page_content)}")
                print(f"内容：{chunk.page_content[:100]}...")

    else:
        print("\n❌ 失败 ")

        print("- 检查 PDF 文件是否损坏")
        print("- 尝试手动打开 PDF 确认文件正常")

    print("\n" + "=" * 60)
    print("💡 LangChain 使用提示:")
    print("=" * 60)
    print("1. PyPDFLoader - 轻量级，适合简单 PDF")
    print("2. PDFPlumberLoader - 中文支持好，推荐 ⭐")
    print("3. PyMuPDFLoader - 性能最好")
    print("4. UnstructuredPDFLoader - 支持 OCR（扫描件）")
    print("\n后续可以用于 RAG、向量存储等场景")
