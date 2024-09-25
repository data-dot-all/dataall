my_array=("$(aws s3api list-buckets --query 'Buckets[?contains(Name, `session`) == `true`].[Name]' --output text)")
array=("${(@f)my_array}")
for YOUR_BUCKET in "${array[@]}"
do

aws s3api delete-objects --bucket ${YOUR_BUCKET} \
--delete "$(aws s3api list-object-versions --bucket ${YOUR_BUCKET} --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"

aws s3api delete-objects --bucket ${YOUR_BUCKET} \
--delete "$(aws s3api list-object-versions --bucket ${YOUR_BUCKET} --query='{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}')"

aws s3api delete-bucket --bucket ${YOUR_BUCKET}
done