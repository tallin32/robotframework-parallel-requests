"""Compatibility stubs for non-prefixed keyword discovery by language servers.

These functions exist to help editors/LSPs index common RequestsLibrary-style names.
They raise NotImplementedError at runtime; users should import the `ParallelRequests` library in Robot tests.
"""

def Create_Session(*args, **kwargs):
    """Create Session - compatibility stub for LSPs"""
    raise NotImplementedError("This stub exists for IDE/LSP indexing. Use the `ParallelRequests` library in Robot tests.")


def Queue_Request(*args, **kwargs):
    """Queue Request - compatibility stub for LSPs"""
    raise NotImplementedError("This stub exists for IDE/LSP indexing. Use the `ParallelRequests` library in Robot tests.")


def Start_Workers(*args, **kwargs):
    """Start Workers - compatibility stub for LSPs"""
    raise NotImplementedError("This stub exists for IDE/LSP indexing. Use the `ParallelRequests` library in Robot tests.")


def Wait_For_All_Requests(*args, **kwargs):
    """Wait For All Requests - compatibility stub for LSPs"""
    raise NotImplementedError("This stub exists for IDE/LSP indexing. Use the `ParallelRequests` library in Robot tests.")


def Get_Response_Object(*args, **kwargs):
    """Get Response Object - compatibility stub for LSPs"""
    raise NotImplementedError("This stub exists for IDE/LSP indexing. Use the `ParallelRequests` library in Robot tests.")
