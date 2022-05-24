
function nii2int16(in_nii, out_nii, normz)

if ~exist('normz','var')
    normz = 1;
elseif ischar(normz)
    normz = str2double(normz);
end

v=load_nii_BIG_Lab(in_nii);

v.hdr.dime.datatype=4; v.hdr.dime.bitpix = 16;

%amin=min(v.img(:)); v.img = v.img - amin;
v.img=double(v.img);

if normz
    amax = max(v.img(:)); v.img = 32000*double(v.img)/amax;
    v.img(v.img<0)=0;
end

save_untouch_nii_gz(v, out_nii);
