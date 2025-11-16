# Import the constant TYPE_HANDSHAKE from the protocol module inside the C2.server package.
# This constant represents the message type used for "handshake" messages in your C2 protocol.
from C2.server.protocol import TYPE_HANDSHAKE


def make_handshake(payload: dict) -> dict:
    # Create and return a dictionary representing a "handshake" message.
    #
    # Args:
    #     payload (dict): The data to include inside the handshake message.
    #                     This can contain any information the client/agent
    #                     wants to send to the server during the initial
    #                     connection phase (e.g. agent ID, hostname, OS, etc.).
    #
    # Returns:
    #     dict: A dictionary with a fixed structure:
    #           {
    #               "type": TYPE_HANDSHAKE,
    #               "payload": <the payload argument>
    #           }
    #           - "type"   : identifies this message as a handshake message,
    #                        using the shared protocol constant TYPE_HANDSHAKE.
    #           - "payload": carries the actual content/data of the handshake.
    #
    # This structure is usually later serialized (e.g. to JSON) and sent over
    # the network from the agent to the C2 server, so both sides can agree on
    # the message format and understand that this is a "handshake" operation.
    return {"type": TYPE_HANDSHAKE, "payload": payload}
