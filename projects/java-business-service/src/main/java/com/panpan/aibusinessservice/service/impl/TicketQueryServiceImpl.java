package com.panpan.aibusinessservice.service.impl;

import com.panpan.aibusinessservice.dto.CurrentUserView;
import com.panpan.aibusinessservice.dto.TicketListItemView;
import com.panpan.aibusinessservice.mapper.TicketMapper;
import com.panpan.aibusinessservice.service.TicketQueryService;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class TicketQueryServiceImpl implements TicketQueryService {
    private final TicketMapper ticketMapper;

    public TicketQueryServiceImpl(TicketMapper ticketMapper) {
        this.ticketMapper = ticketMapper;
    }

    @Override
    public List<TicketListItemView> listVisibleTickets(CurrentUserView currentUser) {
        if (currentUser.roles().contains("customer")) {
            return ticketMapper.selectByTenantIdAndRequesterUserId(currentUser.tenantId(), currentUser.userId())
                    .stream()
                    .map(TicketListItemView::from)
                    .toList();
        }

        return ticketMapper.selectAllByTenantId(currentUser.tenantId())
                .stream()
                .map(TicketListItemView::from)
                .toList();
    }
}
