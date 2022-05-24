istring="/nafs/shattuck/yeunkim/AOMIC-PIOP2/%s/anat/%s_T1w.nii.gz";
ostring="/nafs/shattuck/yeunkim/AOMIC-PIOP2_rescaled/%s_T1w.nii.gz";

% read in IDs from text file
fid = fopen('/nafs/shattuck/yeunkim/processing/AOMIC_PIOP2/allsubjs.txt');
txt = textscan(fid,"%s",'delimiter',"\n"); 
% ids = cellstr((txt{1}));
for i=1:length(txt{1})
    ipath = char(sprintf(istring, string(txt{1}(i)),string(txt{1}(i))));
    opath = char(sprintf(ostring, string(txt{1}(i))));
    nii2int16(ipath, opath);
    disp(ipath);
    disp(opath);
end
