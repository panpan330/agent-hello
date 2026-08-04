package com.panpan.aibusinessservice.service.impl;

import com.panpan.aibusinessservice.dto.CurrentUserView;
import com.panpan.aibusinessservice.dto.KnowledgeDocumentView;
import com.panpan.aibusinessservice.mapper.KnowledgeDocumentMapper;
import com.panpan.aibusinessservice.service.KnowledgeDocumentService;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.springframework.stereotype.Service;

@Service
public class KnowledgeDocumentServiceImpl implements KnowledgeDocumentService {
    private final KnowledgeDocumentMapper knowledgeDocumentMapper;

    public KnowledgeDocumentServiceImpl(KnowledgeDocumentMapper knowledgeDocumentMapper) {
        this.knowledgeDocumentMapper = knowledgeDocumentMapper;
    }

    @Override
    public List<KnowledgeDocumentView> listVisibleDocuments(CurrentUserView currentUser) {
        if (currentUser.roles().contains("admin")) {
            return knowledgeDocumentMapper.selectAllByTenantId(currentUser.tenantId())
                    .stream()
                    .map(KnowledgeDocumentView::from)
                    .toList();
        }

        List<String> permissionGroups = permissionGroupsFor(currentUser.roles());
        return knowledgeDocumentMapper
                .selectVisibleByTenantIdAndPermissionGroups(currentUser.tenantId(), permissionGroups)
                .stream()
                .map(KnowledgeDocumentView::from)
                .toList();
    }

    private List<String> permissionGroupsFor(List<String> roles) {
        Set<String> permissionGroups = new LinkedHashSet<>();
        permissionGroups.add("public");

        if (roles.contains("customer")) {
            permissionGroups.add("customer");
        }
        if (roles.contains("agent") || roles.contains("supervisor")) {
            permissionGroups.add("customer_service");
        }

        return List.copyOf(permissionGroups);
    }
}
