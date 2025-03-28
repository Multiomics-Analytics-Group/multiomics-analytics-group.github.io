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

## Analytics Core (Acore) Library

Acore, short for analytics core, is an open-source Python library 
to preprocess and analyse multi-omics data. It includes functionality related to preprocessing, e.g. for 
data normalization, missing value imputation or feature selection, and functionality for statistical data analysis, e.g. an analysis of covariance.
Acore is designed to be user-friendly and flexible, allowing users to easily apply 
different analysis strategies, testing effects of choosing specific steps.

Especially recipes will help to get started and explore several options for data analysis.

Check out current recipes and the core libary documentation at 
[analytics-core.readthedocs.io](https://analytics-core.readthedocs.io/).

