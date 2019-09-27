from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply


class ResourceAccessManager(QNetworkAccessManager):

    def createRequest(self, operation, request, outgoingdata):
        if request.url().scheme() == 'pyrc':
            return ResourceNetworkReply(operation, request)
        return super().createRequest(operation, request, outgoingdata)

    def supportedSchemesImplementation(self):
        return super().supportedSchemesImplementation() + ['pyrc']


class ResourceNetworkReply(QNetworkReply):

    def __init__(self, operation, request):
        super().__init__()
