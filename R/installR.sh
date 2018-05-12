#!/bin/bash

cd /BrainSuite/R/
wget https://cran.r-project.org/src/contrib/Archive/pander/pander_0.6.0.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/markdown/markdown_0.7.7.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/DT/DT_0.2.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/ini/ini_0.1.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/RColorBrewer/RColorBrewer_1.0-5.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/RNifti/RNifti_0.5.1.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/ggplot2/ggplot2_2.2.0.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/scales/scales_0.4.1.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/doParallel/doParallel_1.0.8.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/foreach/foreach_1.4.2.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/bit/bit_1.1-11.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/Matrix/Matrix_1.2-10.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/digest/digest_0.6.11.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/Rcpp/Rcpp_0.12.11.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/mime/mime_0.4.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/htmltools/htmltools_0.3.5.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/htmlwidgets/htmlwidgets_0.8.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/magrittr/magrittr_1.0.1.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/jsonlite/jsonlite_1.4.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/yaml/yaml_2.1.13.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/gtable/gtable_0.1.2.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/MASS/MASS_7.3-46.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/plyr/plyr_1.8.3.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/reshape2/reshape2_1.4.1.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/tibble/tibble_1.3.3.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/lazyeval/lazyeval_0.2.0.tar.gz
wget https://cran.r-project.org/src/contrib/R6_2.2.2.tar.gz

# for scales:
wget https://cran.r-project.org/src/contrib/Archive/dichromat/dichromat_1.2-4.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/munsell/munsell_0.4.2.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/labeling/labeling_0.2.tar.gz

# for reshape2
wget https://cran.r-project.org/src/contrib/Archive/colorspace/colorspace_1.3-1.tar.gz

# for tibble
wget https://cran.r-project.org/src/contrib/Archive/rlang/rlang_0.1.1.tar.gz

wget https://cran.r-project.org/src/contrib/Archive/stringr/stringr_1.1.0.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/stringi/stringi_1.1.3.tar.gz

# for doparallel
wget https://cran.r-project.org/src/contrib/Archive/iterators/iterators_1.0.7.tar.gz

# for foreach
wget https://cran.r-project.org/src/contrib/Archive/codetools/codetools_0.2-14.tar.gz

# for Matrix
wget https://cran.r-project.org/src/contrib/Archive/lattice/lattice_0.20-34.tar.gz

# for bssr
wget https://cran.r-project.org/src/contrib/Archive/rmarkdown/rmarkdown_1.5.tar.gz

# for rmarkdown
wget https://cran.r-project.org/src/contrib/Archive/knitr/knitr_1.16.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/caTools/caTools_1.17.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/evaluate/evaluate_0.10.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/base64enc/base64enc_0.1-2.tar.gz
wget https://cran.r-project.org/src/contrib/Archive/rprojroot/rprojroot_1.1.tar.gz

# for knitr
#evaluate
wget https://cran.r-project.org/src/contrib/Archive/highr/highr_0.5.1.tar.gz

# for caTools
wget https://cran.r-project.org/src/contrib/Archive/bitops/bitops_1.0-5.tar.gz

# for rprojr
wget https://cran.r-project.org/src/contrib/Archive/backports/backports_1.0.5.tar.gz

##TODO: figure out proper order

for i in `cat /BrainSuite/R/Rpackages.txt`; do
    R CMD INSTALL $i;
done
