import { Box, Fab, Tooltip } from '@mui/material';
import { useState, Children, cloneElement } from 'react'; //useEffect
import ChatIcon from '@mui/icons-material/Chat';
import { Chatbot, createChatBotMessage } from 'react-chatbot-kit';
import { useClient } from 'services';
// import { SET_ERROR } from 'globalErrors';
import './chatbot.css';
import 'react-chatbot-kit/build/main.css';
import { sendQueryChatbot } from 'services/graphql/Chatbot/sendQueryChatbot';

const config = {
  lang: 'en',
  botName: 'DataallBot',
  initialMessages: [
    createChatBotMessage(
      `Hi, I'm here to provide you with help navigating data.all!`
    )
  ],
  state: {}
};

const ActionProvider = ({ createChatBotMessage, setState, children }) => {
  const client = useClient();

  const handleQuery = (message) => {
    const response = client.mutate(
      sendQueryChatbot({
        queryString: message
      })
    );

    response.then((res) => {
      let botResponse = '';

      if (!res.errors) {
        console.error('RESPONSE');

        console.error(res);
        botResponse = res.data.sendQueryChatbot.response;
      } else {
        botResponse =
          'I am sorry I am having trouble answering that question, is there anything else I can help you with?';
      }
      const botMessage = createChatBotMessage(botResponse);
      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, botMessage]
      }));
    });
  };
  return (
    <div>
      {Children.map(children, (child) => {
        return cloneElement(child, { actions: { handleQuery } });
      })}
    </div>
  );
};
const MessageParser = ({ children, actions }) => {
  const parse = (message) => {
    console.error(message);
    actions.handleQuery(message);
  };

  return (
    <div>
      {Children.map(children, (child) => {
        return cloneElement(child, { parse: parse, actions: {} });
      })}
    </div>
  );
};

export const DataallChatbot = () => {
  const [showBot, toggleBot] = useState(false);

  // useEffect(() => {
  // }, []);

  // const handleOpen = () => {
  //   setOpen(true);
  // };

  // const handleClose = () => {
  //   setOpen(false);
  // };

  return (
    <>
      <Box
        sx={{
          zIndex: 1300
        }}
      >
        <Tooltip title="Open Chatbot">
          <Fab
            className="app-chatbot-button"
            color="primary"
            onClick={() => toggleBot((prev) => !prev)}
          >
            <ChatIcon fontSize="large" />
          </Fab>
        </Tooltip>
        {showBot && (
          <div className="app-chatbot-container">
            <Chatbot
              config={config}
              messageParser={MessageParser}
              actionProvider={ActionProvider}
            />
          </div>
        )}
      </Box>
    </>
  );
};

DataallChatbot.propTypes = {};
