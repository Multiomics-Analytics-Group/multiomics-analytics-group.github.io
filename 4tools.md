---
layout: page
title: Tools
permalink: /tools/
---

# Clinical Knowledge Graph -- CKG

## Integrating and Interpreting MS-based Proteomics Data

The Clinical Knowledge Graph (CKG) is a graph database with millions of nodes and relationships representing experimental data, databases, and scientific literature. Further, CKG is an open-source platform that allows easy expansion with new databases and experimental data types and it includes statistical and machine learning tools for faster proteomics analysis. 

We are currently working on a new version that will be more flexible and generalizable. **Stay tuned!**

<img src="{{ site.baseurl }}/public/ckg.jpeg" style="width:100%">


# OrthoHPI 2.0 [[link]](https://orthohpi.streamlit.app/)

## Orthology–based Host–Parasite Protein–protein Interactions

Understanding host-parasite interactions is vital for tackling infectious diseases. Due to the challenges in experimental identification, we propose a computational method to predict protein interactions between human and 18 eukaryotic parasites. Our approach leverages an orthology-based transfer of interactions, focusing on parasite secretomes and human membrane proteins. We also filter the host proteome based on the parasites' specific tissue tropisms. In this version, we added  cell-type specific expression annotations to provide further resolution of the host-parasite predicted interactions and we support interactions with structural information.

### Giardia intestinalis Predicted PPI
<iframe src="{{ site.baseurl }}/public/Gi_network.html" width="600" height="450" style="border:0;"></iframe>

# Analytics Core (Acore) Library

Acore, short for analytics core, is an open-source Python library 
to preprocess and analyse multi-omics data. It includes functionality related to preprocessing, e.g. for 
data normalization, missing value imputation or feature selection, and functionality for statistical data analysis, e.g. an analysis of covariance.
Acore is designed to be user-friendly and flexible, allowing users to easily apply 
different analysis strategies, testing effects of choosing specific steps.

Especially recipes will help to get started and explore several options for data analysis.

Check out current recipes and the core libary documentation at 
[analytics-core.readthedocs.io](https://analytics-core.readthedocs.io/).

<div style="text-align: center; margin-bottom: 20px;">
  <a href="https://github.com/Multiomics-Analytics-Group/vuegen" target="_blank">
    <img src="https://raw.githubusercontent.com/Multiomics-Analytics-Group/vuegen/main/docs/images/vuegen_logo.svg" alt="VueGen" width="250px">
  </a>
</div>

**VueGen** is a tool that automates the creation of **reports** from bioinformatics outputs, allowing researchers with minimal coding experience to communicate their results effectively. With VueGen, users can produce reports by simply specifying a directory containing output files, such as plots, tables, networks, Markdown text, HTML components, and API calls, along with the report format. Supported formats include **documents** (PDF, HTML, DOCX, ODT), **presentations** (PPTX, Reveal.js), **Jupyter notebooks**, and [Streamlit](https://streamlit.io/) **web applications**.

An overview of the VueGen workflow is shown in the figure below:

![VueGen Abstract](https://raw.githubusercontent.com/Multiomics-Analytics-Group/vuegen/main/docs/images/vuegen_graph_abstract.png)

VueGen offers various implementation options for both non-technical and experienced users. It is available as a [Python package](https://pypi.org/project/vuegen/), [Docker image](https://quay.io/repository/dtu_biosustain_dsp/vuegen), [nf-core module](https://github.com/Multiomics-Analytics-Group/nf-vuegen/), and [cross-platform desktop application](https://github.com/Multiomics-Analytics-Group/vuegen/releases/tag/v0.3.2) with a user-friendly interface, making it accessible and customizable for different user needs and expertise levels.

The documentation is available at [vuegen.readthedocs.io](https://vuegen.readthedocs.io/), where you can find detailed information of the package’s classes and functions, installation and execution instructions, and case studies to demonstrate its functionality.
