# import logging
# from cornice.service import Service
# from fabrikApi.views.lib.factories import ContentManagerFactory
# from fabrikApi.models.contenttree.content_peerreview import DBContentPeerReview, \
#      initiate_peer_review

# logger = logging.getLogger(__name__)

# service_content_propose_delete = Service(
#     cors_origins=('*',),
#     name='service_content_delete_propose',
#     description='Propose to delete a content.',
#     path='/assembly/{assembly_identifier}/content/{content_id:\d+}/propse_delete',
#     traverse='/{content_id}',
#     factory=ContentManagerFactory)

# # @service_content_propose_delete.post(permission='propose_modify')
# # def content_delete_propose(request):
# #     """Propose to delete an entry!"""

# #     assert request.content.patched, "content should be patched here.."
# #     assert request.content.COMMON_PROPERTY_CONTENT, "method is made for common property content only."
# #     assert request.json_body['justification'], "justification is missing...."

# #     # Open new Delete Peer Review
# #     new_proposal = initiate_peer_review(
# #         request,
# #         operation=DBContentPeerReview.DELETE,
# #         content=request.content,
# #         user_id=request.local_userid,
# #         data_to_apply_on_success={'disabled': True}  # Close peerreview flag after peer review finalization
# #     )

# #     return({
# #         'OK': True,
# #         'proposal': new_proposal
# #     })
