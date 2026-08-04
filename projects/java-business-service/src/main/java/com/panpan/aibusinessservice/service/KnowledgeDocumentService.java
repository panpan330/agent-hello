package com.panpan.aibusinessservice.service;

import com.panpan.aibusinessservice.dto.CurrentUserView;
import com.panpan.aibusinessservice.dto.KnowledgeDocumentView;
import java.util.List;

public interface KnowledgeDocumentService {
    List<KnowledgeDocumentView> listVisibleDocuments(CurrentUserView currentUser);
}
