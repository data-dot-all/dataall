import { gql } from 'apollo-boost';

const removeDatasetLoader = ({ loaderUri }) => ({
  variables: { loaderUri },
  mutation: gql`mutation RemoveDatasetLoader(
            $loaderUri:String
        ){
            removeDatasetLoader(
                loaderUri:$loaderUri,
            )
        }`
});

export default removeDatasetLoader;
