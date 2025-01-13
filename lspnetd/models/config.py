from pydantic import BaseModel


class WireGuardKeySchema(BaseModel):
    namespace: str
    name: str
    public_key: str
    private_key: str
    

class WireGuardPeerSchema(BaseModel):
    namespace: str
    name: str
    public_key: str
    is_static_key: int
    endpoint: str
    is_static_endpoint: int
